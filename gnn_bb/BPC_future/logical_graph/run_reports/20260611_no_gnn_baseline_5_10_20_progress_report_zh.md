# 5/10/20 no-GNN baseline 全量运行进度报告

生成时间：2026-06-11 00:18 左右；00:25 更新 20 规模并发运行策略。  
报告性质：进度版，不是最终验收版。20 规模全量 60 个实例仍在运行中。

## 执行边界

- 运行目标：5、10、20 规模全量 no-GNN baseline。
- 时间限制：5/10 规模 600 秒；20 规模 3600 秒。
- no-GNN 覆盖参数：
  - `journey_learning_enabled=False`
  - `journey_learning_required=False`
  - `journey_learning_fail_hard=False`
  - `journey_learning_force_light_profile_pricing=False`
  - `journey_learning_prewarm_enabled=False`
  - `journey_learning_pricing_enabled=False`
- 20 规模先用单实例外部 `timeout --kill-after 30s 3600s` 推进；确认前三个实例均超时后，已切换为 `max-workers=4` 的并发外部 timeout 批处理，避免串行跑满 60 个实例耗时过长。
- 并发批处理仍由单个 Python controller 管理 CSV 写入，不存在多个进程同时写同一结果文件。
- 本报告只记录当前状态；没有停止 20 规模运行。

## 产物路径

- 5 规模 CSV：`BPC_future/results/20260610_post360_tasks5_no_gnn_baseline.csv`
- 10 规模 CSV：`BPC_future/results/20260610_post360_tasks10_no_gnn_baseline.csv`
- 20 规模早期串行外部 timeout CSV：`BPC_future/results/20260610_post360_tasks20_no_gnn_baseline_external_timeout.csv`
- 20 规模当前并发外部 timeout CSV：`BPC_future/results/20260611_post360_tasks20_no_gnn_baseline_external_timeout_parallel.csv`
- 20 规模当前并发 JSONL 日志目录：`BPC_future/results/logs/20260611_post360_tasks20_no_gnn_baseline_external_timeout_parallel`
- 20 规模当前并发 controller 日志：`BPC_future/results/20260611_post360_tasks20_no_gnn_baseline_external_timeout_parallel_controller.log`

## 当前完成度

| 规模 | 目标实例数 | 当前CSV行数 | 状态 |
| ---: | ---: | ---: | --- |
| 5 | 60 | 60 | 完成，60/60 OPTIMAL |
| 10 | 60 | 60 | 完成，60/60 OPTIMAL |
| 20 | 60 | 3 | 进行中，前 3 个均为 EXTERNAL_TIME_LIMIT；当前并发跑第 4-7 个实例 |

## 5规模结果

- 状态：`OPTIMAL: 60`
- 求解时间：
  - min：0.232879 s
  - mean：0.346673 s
  - median：0.306467 s
  - p90：0.404405 s
  - max：1.416103 s
- 平均节点数：1.067
- 平均 RMP solves：1.950
- 平均 pricing calls：4.583
- 平均 exact pricing calls：3.517
- 平均 generated sequences：1952.267
- 平均 evaluated timed trips：901.733
- 平均 columns：16.517

最慢 5 个实例：

| time(s) | status | instance | obj | nodes | pricing_calls | generated_sequences |
| ---: | --- | --- | ---: | ---: | ---: | ---: |
| 1.416103 | OPTIMAL | `apollo15_20km_greedy-anchor_randomtw_tasks005_01_seed46001_logical_graph.json` | 231.639865 | 1 | 4 | 935 |
| 0.867765 | OPTIMAL | `apollo15_20km_random-wave_randomtw_tasks005_03_seed1046207_logical_graph.json` | 231.991886 | 3 | 12 | 5571 |
| 0.837895 | OPTIMAL | `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_08_seed2146729_logical_graph.json` | 227.481205 | 3 | 12 | 4758 |
| 0.441865 | OPTIMAL | `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks005_03_seed146214_logical_graph.json` | 180.626947 | 1 | 6 | 3755 |
| 0.425889 | OPTIMAL | `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks005_02_seed146110_logical_graph.json` | 186.931792 | 1 | 11 | 3802 |

评价：5 规模 no-GNN baseline 很稳定，所有实例远低于 600 秒。节点数和 pricing 次数都很小，说明新时间窗/能量约束在 5 规模下没有制造异常难例。

## 10规模结果

- 状态：`OPTIMAL: 60`
- 求解时间：
  - min：1.336001 s
  - mean：5.032708 s
  - median：1.723952 s
  - p90：9.174236 s
  - max：53.040080 s
- 平均节点数：3.133
- 平均 RMP solves：6.133
- 平均 pricing calls：12.950
- 平均 exact pricing calls：12.950
- 平均 generated sequences：15881.683
- 平均 evaluated timed trips：5199.417
- 平均 columns：65.567

最慢 5 个实例：

| time(s) | status | instance | obj | nodes | pricing_calls | generated_sequences |
| ---: | --- | --- | ---: | ---: | ---: | ---: |
| 53.040080 | OPTIMAL | `tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks010_06_seed51521_logical_graph.json` | 338.615584 | 29 | 110 | 223160 |
| 47.010861 | OPTIMAL | `tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks010_04_seed51316_logical_graph.json` | 339.286391 | 33 | 113 | 162745 |
| 34.827974 | OPTIMAL | `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks010_10_seed51929_logical_graph.json` | 330.360353 | 21 | 79 | 116223 |
| 26.778574 | OPTIMAL | `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_09_seed51864_logical_graph.json` | 352.168131 | 15 | 52 | 124572 |
| 18.129242 | OPTIMAL | `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks010_08_seed51725_logical_graph.json` | 350.738862 | 13 | 53 | 60240 |

评价：10 规模 no-GNN baseline 也完成 60/60，最慢 53.04 秒，仍低于 600 秒。慢例集中在 `tranquillitatis_balmer_like_20km`，表现为节点数、pricing calls 和 generated sequences 同时上升，说明主要压力来自 branch/tree 与 pricing 交互，而不是单纯 RMP 求解。

## 20规模当前状态

当前 CSV 已落盘 3 行：

| # | instance | status | return_code | wall_time(s) |
| ---: | --- | --- | ---: | ---: |
| 1 | `apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json` | EXTERNAL_TIME_LIMIT | 143 | 3920 |
| 2 | `apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json` | EXTERNAL_TIME_LIMIT | 124 | 3600.009469 |
| 3 | `apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json` | EXTERNAL_TIME_LIMIT | 124 | 3600.020057 |

早期串行第 4 个实例曾运行约 11 分钟，未落盘；为避免 60 个实例串行耗时过长，已终止旧串行 controller 并切换到新并发 controller。当前并发运行中实例：

- `apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json`
- `apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json`
- `apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json`
- `apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph.json`

并发切换后的内存观察：

- 系统可用内存约 10 GiB。
- 4 个 20 规模子进程启动初期 RSS 约 206-219 MB/进程，后续仍需持续观察。

已观察到的 20 规模瓶颈：

- 前 3 个实例均没有正常证明最优，均由外部 timeout 杀掉并写入 `EXTERNAL_TIME_LIMIT`。
- 这些实例不是在数据加载、GNN、RMP 初期、普通 worker 阶段卡住。
- 日志显示它们均进入 true-dual completion-bound final judge / `journey_exact_pricing_completion_bound_retry` 后长时间无法返回最终证明。
- 当前 baseline 中：
  - `completion_bound_mode="bucket"`
  - `unique_route_exact_first_step=true`
  - `unique_route_helper=true`
  - `unique_task_helper=true`
  - `two_cycle=true`
  - `completion_bound_diverse_harvest=true`
  - `resource_pareto_completion=false`
  - `available_mask_completion_bound=false`
  - `amcb_enabled=false`
  - `rpce_enabled=false`

## no-GNN 验证

对 5/10/20 当前日志目录搜索 `journey_learning|gnn|learning` 未发现事件。结合运行覆盖参数，本轮结果可视为 no-GNN baseline。

## 内存观察

当前内存不是主要瓶颈：

- 总内存约 15 GiB。
- 串行阶段可用内存约 11 GiB；并发切换后可用内存约 10 GiB。
- 串行阶段单个 20 规模求解子进程 RSS 曾约 574 MB；并发启动初期 4 个子进程约 206-219 MB/进程，后续仍需持续观察峰值。
- 前几个 20 规模实例超时时也没有观察到内存耗尽迹象。

## 初步问题来源分析

1. 5/10 规模已证明 baseline 稳定：全量完成，最慢 10 规模实例 53 秒。
2. 20 规模开始出现质变：同样配置下，前几个实例早期能推进 CG，但最终卡在 true-dual completion-bound final judge 的证明路径。
3. 问题不是 GNN，因为 GNN 已关闭且日志无 learning 事件。
4. 问题不是 RPCE/AMCB 负优化，因为当前 20 baseline 中两者均关闭。
5. 问题更接近 exact pricing proof path 的搜索规模爆炸：时间窗和能量约束足够让普通 worker 找列，但不足以让 final judge 快速证明 no negative。
6. `EXTERNAL_TIME_LIMIT` 行不是最优解，也不提供 lower-bound certificate；它们只表示外部 3600 秒硬超时。

## 后续动作

- 继续让 20 规模外部 timeout 批处理跑完 60 个实例。
- 每个实例完成后 CSV 会立即追加一行，避免整批结果丢失。
- 20 CSV 满 60 行后，更新本报告为最终验收版：
  - 20 规模 status 计数。
  - OPTIMAL / EXTERNAL_TIME_LIMIT 分布。
  - 分地形、分时间窗模式的耗时与失败分布。
  - final judge retry 触发位置和日志归因。
  - 5/10/20 的统一评价。

## 2026-06-11 00:36 CST 续跑检查

- 5 规模 CSV 仍为 `60` 行，状态 `OPTIMAL: 60`。
- 10 规模 CSV 仍为 `60` 行，状态 `OPTIMAL: 60`。
- 20 规模当前并发 CSV 仍为 `3` 行，状态 `EXTERNAL_TIME_LIMIT: 3`。
- 20 规模并发 controller 正在运行，当前 worker 仍是第 4-7 个实例：
  - `apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json`
  - `apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json`
  - `apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json`
  - `apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph.json`
- 内存观察：系统约 `15 GiB`，可用约 `10 GiB`；4 个 20 规模 worker RSS 大约 `335-573 MiB/进程`，当前没有内存耗尽迹象。
- JSONL 日志确认第 4-7 个实例均已进入 `journey_exact_pricing_completion_bound_retry`，并且：
  - `completion_bound_mode="bucket"`
  - `completion_bound_diverse_harvest=true`
  - `completion_bound_unique_route_exact_first_step=true`
  - `resource_pareto_completion=false`
  - `available_mask_completion_bound=false`
  - `rpce_enabled=false`
  - `amcb_enabled=false`
- 当前归因保持不变：20 规模主要卡在 true-dual completion-bound final judge 证明/收割路径，不是 GNN、RPCE/AMCB、数据加载或内存问题。

## 2026-06-11 01:30 CST 续跑检查

- 20 规模当前并发 CSV 已追加到 `7` 行，状态计数：
  - `EXTERNAL_TIME_LIMIT: 3`
  - `TIME_LIMIT: 4`
- 第 4-7 个实例均由 solver 内部时间限制返回，`return_code=0`，wall time 约 `3481s`；它们不是 external kill，但也不是 `OPTIMAL`，不提供最优证书。

| # | instance | status | return_code | wall_time(s) | solving_time(s) |
| ---: | --- | --- | ---: | ---: | ---: |
| 4 | `apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json` | TIME_LIMIT | 0 | 3480.749227 | 3480.098466 |
| 5 | `apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json` | TIME_LIMIT | 0 | 3481.653233 | 3480.577568 |
| 6 | `apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json` | TIME_LIMIT | 0 | 3481.311573 | 3480.151249 |
| 7 | `apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph.json` | TIME_LIMIT | 0 | 3481.065372 | 3480.081077 |

- Controller 已自动启动第 8-11 个实例：
  - `apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json`
  - `apollo15_20km_greedy-anchor_randomtw_tasks020_09_seed61818_logical_graph.json`
  - `apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json`
  - `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json`
- 当前内存仍稳定：系统可用约 `10 GiB`；第 8-11 个 worker 启动初期 RSS 约 `262-344 MiB/进程`。
- 观察到的模式更明确：20 规模的 apollo / greedy-anchor 开头连续 7 个实例均未在 3600 秒窗口内证明最优。问题不是个别坏 seed，而是该规模和该分布下的 proof-path 长尾。

## 2026-06-11 01:45 CST 续跑检查

- 5 规模 CSV 仍为 `60` 行，状态 `OPTIMAL: 60`。
- 10 规模 CSV 仍为 `60` 行，状态 `OPTIMAL: 60`。
- 20 规模当前并发 CSV 仍为 `7` 行，状态计数：
  - `EXTERNAL_TIME_LIMIT: 3`
  - `TIME_LIMIT: 4`
- 20 规模 batch controller 仍在运行，当前第 8-11 个 worker 已运行约 `15` 分钟：
  - `apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json`
  - `apollo15_20km_greedy-anchor_randomtw_tasks020_09_seed61818_logical_graph.json`
  - `apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json`
  - `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json`
- 当前内存仍稳定：系统约 `15 GiB`，可用约 `10 GiB`；4 个 20 规模 worker RSS 约 `262-680 MiB/进程`。
- 暂无异常中断，因此没有执行恢复重启；继续等待 20 规模批处理追加结果。

## 2026-06-11 02:35 CST 续跑检查

- 20 规模当前并发 CSV 已追加到 `11` 行，状态计数：
  - `EXTERNAL_TIME_LIMIT: 5`
  - `TIME_LIMIT: 6`
  - `OPTIMAL: 0`
- 第 8-11 个实例完成后，controller 已自动启动第 12-15 个实例。
- 第 8 和第 10 个实例由 solver 内部时间限制返回，`return_code=0`，wall time 约 `3481s`；第 9 和第 11 个实例由外部 3600 秒 timeout 返回，`return_code=124`。

| # | instance | status | return_code | wall_time(s) | solving_time(s) | node_count | pricing_calls | generated_sequences |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 8 | `apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json` | TIME_LIMIT | 0 | 3481.501160 | 3480.549812 | 1 | 17 | 657374 |
| 9 | `apollo15_20km_greedy-anchor_randomtw_tasks020_09_seed61818_logical_graph.json` | EXTERNAL_TIME_LIMIT | 124 | 3600.020010 |  |  |  |  |
| 10 | `apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json` | TIME_LIMIT | 0 | 3481.385259 | 3480.664744 | 1 | 31 | 1761998 |
| 11 | `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json` | EXTERNAL_TIME_LIMIT | 124 | 3600.007170 |  |  |  |  |

- 当前第 12-15 个 worker：
  - `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json`
  - `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json`
  - `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json`
  - `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json`
- 内存仍稳定：系统约 `15 GiB`，可用约 `10 GiB`；第 12-15 个 worker 启动初期 RSS 约 `263-285 MiB/进程`。
- 新增证据强化了当前归因：20 规模仍停在 root-level exact pricing / completion-bound final judge 证明成本上，第 8 和第 10 个实例的 `node_count=1` 但 `generated_sequences` 分别达到约 `65.7万` 和 `176.2万`。

## 2026-06-11 03:38 CST 续跑检查

- 20 规模当前并发 CSV 已追加到 `13` 行，状态计数：
  - `EXTERNAL_TIME_LIMIT: 5`
  - `TIME_LIMIT: 8`
  - `OPTIMAL: 0`
- 第 12 和第 13 个实例均由 solver 内部时间限制返回，`return_code=0`，仍是 root node 未证优。

| # | instance | status | return_code | wall_time(s) | solving_time(s) | node_count | pricing_calls | generated_sequences |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 12 | `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json` | TIME_LIMIT | 0 | 3480.832056 | 3480.115799 | 1 | 14 | 620761 |
| 13 | `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json` | TIME_LIMIT | 0 | 3480.697382 | 3480.041257 | 1 | 13 | 647537 |

- 第 14 和第 15 个实例仍在运行，已接近 1 小时；第 16 和第 17 个实例已由 controller 自动启动。
- 内存仍稳定：系统约 `15 GiB`，可用约 `10 GiB`；当前运行中的 20 规模 worker RSS 约 `256-316 MiB/进程`。
- 当前 13 个已落盘 20 规模实例全部未证优。8 个内部 `TIME_LIMIT` 行中，已记录 `node_count` 的实例均为 `1`，进一步支持“根节点 exact pricing/proof 长尾”而不是“分支树扩张”的诊断。

## 2026-06-11 05:47 CST 续跑检查

- 20 规模当前并发 CSV 已追加到 `21` 行，状态计数：
  - `OPTIMAL: 1`
  - `TIME_LIMIT: 10`
  - `EXTERNAL_TIME_LIMIT: 10`
- `greedy-anchor` 模式 20 个实例已全部落盘：
  - `apollo15_20km`: `OPTIMAL: 0 / 10`，`TIME_LIMIT: 6`，`EXTERNAL_TIME_LIMIT: 4`。
  - `tranquillitatis_balmer_like_20km`: `OPTIMAL: 1 / 10`，`TIME_LIMIT: 3`，`EXTERNAL_TIME_LIMIT: 6`。
  - 合计 `OPTIMAL: 1 / 20`，明显不满足 20 规模目标。
- 第一个 `random-wave / apollo15_20km` 实例也已落盘，状态为内部 `TIME_LIMIT`。

| # | instance | status | return_code | wall_time(s) | solving_time(s) | node_count | pricing_calls | generated_sequences |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 20 | `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_10_seed61948_logical_graph.json` | OPTIMAL | 0 | 2856.984424 | 2856.250944 | 1 | 11 | 415469 |
| 21 | `apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json` | TIME_LIMIT | 0 | 3480.921167 | 3480.142188 | 1 | 12 | 589034 |

- 第 20 个实例说明当前模型并非完全不能证优；但 20 个 greedy-anchor 中只有 1 个证优，核心问题仍是绝大多数实例的 root-level exact pricing / completion-bound proof 在 3600 秒窗口内无法完成。
- 内存观察：进入 `random-wave` 后第 22 个 worker RSS 曾达到约 `2.13 GiB`，系统可用约 `8.8 GiB`，暂时仍可控，但比 greedy-anchor 阶段更需要持续监控。

## 2026-06-11 08:02 CST 续跑检查

- 20 规模当前并发 CSV 已追加到 `33` 行，状态计数：
  - `OPTIMAL: 5`
  - `TIME_LIMIT: 13`
  - `EXTERNAL_TIME_LIMIT: 15`
- `random-wave / apollo15_20km` 10 个实例已全部落盘：
  - `OPTIMAL: 3 / 10`
  - `TIME_LIMIT: 3 / 10`
  - `EXTERNAL_TIME_LIMIT: 4 / 10`
- `random-wave / tranquillitatis_balmer_like_20km` 当前前 3 个实例已落盘：
  - `OPTIMAL: 1`
  - `TIME_LIMIT: 1`
  - `EXTERNAL_TIME_LIMIT: 1`

| profile/terrain | finished | OPTIMAL | TIME_LIMIT | EXTERNAL_TIME_LIMIT |
| --- | ---: | ---: | ---: | ---: |
| `greedy-anchor / apollo15_20km` | 10 | 0 | 6 | 4 |
| `greedy-anchor / tranquillitatis_balmer_like_20km` | 10 | 1 | 3 | 6 |
| `random-wave / apollo15_20km` | 10 | 3 | 3 | 4 |
| `random-wave / tranquillitatis_balmer_like_20km` | 3 | 1 | 1 | 1 |

- 观察：`random-wave / apollo15_20km` 明显优于 `greedy-anchor / apollo15_20km`，但仍只有 `3/10` 证优，远低于“20 规模最多 1 个未最优”的目标。
- 内存观察：第 22 个 `random-wave / apollo15_20km` worker 曾达到约 `2.16 GiB` RSS，但结束后系统可用内存恢复到约 `10 GiB`；目前没有内存耗尽证据。

## 2026-06-11 10:16 CST 续跑检查

- 20 规模当前并发 CSV 已追加到 `42` 行，状态计数：
  - `OPTIMAL: 8`
  - `TIME_LIMIT: 16`
  - `EXTERNAL_TIME_LIMIT: 18`
- `random-wave` 模式 20 个实例已全部落盘：
  - `apollo15_20km`: `OPTIMAL: 3 / 10`，`TIME_LIMIT: 3`，`EXTERNAL_TIME_LIMIT: 4`。
  - `tranquillitatis_balmer_like_20km`: `OPTIMAL: 3 / 10`，`TIME_LIMIT: 4`，`EXTERNAL_TIME_LIMIT: 3`。
  - 合计 `OPTIMAL: 6 / 20`。
- `sector-wave / apollo15_20km` 当前已有 2 个落盘：
  - `OPTIMAL: 1`
  - `EXTERNAL_TIME_LIMIT: 1`

| profile/terrain | finished | OPTIMAL | TIME_LIMIT | EXTERNAL_TIME_LIMIT |
| --- | ---: | ---: | ---: | ---: |
| `greedy-anchor / apollo15_20km` | 10 | 0 | 6 | 4 |
| `greedy-anchor / tranquillitatis_balmer_like_20km` | 10 | 1 | 3 | 6 |
| `random-wave / apollo15_20km` | 10 | 3 | 3 | 4 |
| `random-wave / tranquillitatis_balmer_like_20km` | 10 | 3 | 4 | 3 |
| `sector-wave / apollo15_20km` | 2 | 1 | 0 | 1 |

- 观察：`random-wave` 比 `greedy-anchor` 明显容易一些，但 `6/20` 证优仍远低于目标。20 规模的瓶颈不是某一个时间窗模式独有，而是规模放大后 exact pricing/proof path 的普遍长尾。
- 内存观察：当前系统可用约 `10 GiB`，没有内存耗尽证据。
