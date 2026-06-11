# 10规模随机时间窗实例 No-GNN Baseline 报告

生成日期：2026-06-10。报告语言：中文。

## 输入与边界

- 实例入口：`BPC_future/logical_graph/tasks_010/`
- 结果 CSV：`BPC_future/results/20260610_tasks10_ablation_no_gnn_baseline.csv`
- 运行日志：`BPC_future/results/20260610_tasks10_ablation_no_gnn_baseline_run.log`
- 校验 JSON：`BPC_future/results/20260610_tasks5_tasks10_logical_graph_post_dedup_validation.json`
- 基础配置：`BPC_future/configs/moon_trek_10_journey.yaml`
- 显式 no-GNN 覆盖：`journey_learning_enabled=False`、`journey_learning_required=False`、`journey_learning_fail_hard=False`、`journey_learning_force_light_profile_pricing=False`、`journey_learning_prewarm_enabled=False`、`journey_learning_pricing_enabled=False`。
- 单实例 time limit：`600s`；评价时单独统计是否超过 `60s`。

## 实例文件检查

- post-dedup 校验问题数：`0`
- canonical logical graph JSON 数：`120`
- generated 源目录残留 logical graph JSON 数：`0`
- 校验实例数：`120`，其中 5规模和10规模各 60 个。
- 10规模每个实例均为完整 directed graph：11 nodes / 110 directed pair edges。
- `manifest.json`、`BPC_future/logical_graph/index.json`、GNN `meta/*.json` 与 `.pt` 字典中的 `logical_graph_path` 已统一指向 `BPC_future/logical_graph/...`。

## 求解总览

- 状态计数：`OPTIMAL:60`
- 全部 60 个实例均为 `OPTIMAL`。
- 求解时间：mean `5.031s`，median `1.704s`，p90 `9.427s`，max `52.723s`。
- 超过 60s 的实例数：`0`。
- 节点数：mean `3.133`，max `33`。
- 平均 pricing calls：`12.950`；平均 exact pricing calls：`12.950`；平均列数：`65.567`。

## 按时间窗模式汇总

| 模式 | n | 状态 | mean time | median | p90 | max | >60s | mean nodes | max nodes | mean pricing | mean exact | mean columns |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| greedy-anchor | 20 | OPTIMAL:20 | 5.196 | 1.880 | 12.145 | 34.696 | 0 | 3.200 | 21 | 14.250 | 14.250 | 76.150 |
| random-wave | 20 | OPTIMAL:20 | 6.583 | 1.626 | 7.652 | 52.723 | 0 | 4.100 | 33 | 16.050 | 16.050 | 57.500 |
| sector-wave | 20 | OPTIMAL:20 | 3.313 | 1.612 | 3.538 | 26.743 | 0 | 2.100 | 15 | 8.550 | 8.550 | 63.050 |

## 按地形与模式汇总

| 地形 | 模式 | n | 状态 | mean time | median | p90 | max | >60s | mean nodes | max nodes | mean pricing | mean exact | mean columns |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| apollo15_20km | greedy-anchor | 10 | OPTIMAL:10 | 2.164 | 1.701 | 2.371 | 6.636 | 0 | 1.400 | 5 | 6.200 | 6.200 | 53.700 |
| apollo15_20km | random-wave | 10 | OPTIMAL:10 | 1.658 | 1.458 | 1.913 | 3.208 | 0 | 1.200 | 3 | 4.800 | 4.800 | 36 |
| apollo15_20km | sector-wave | 10 | OPTIMAL:10 | 1.649 | 1.524 | 1.825 | 2.909 | 0 | 1.200 | 3 | 4.900 | 4.900 | 45.100 |
| tranquillitatis_balmer_like_20km | greedy-anchor | 10 | OPTIMAL:10 | 8.228 | 2.764 | 19.595 | 34.696 | 0 | 5 | 21 | 22.300 | 22.300 | 98.600 |
| tranquillitatis_balmer_like_20km | random-wave | 10 | OPTIMAL:10 | 11.507 | 1.880 | 48.152 | 52.723 | 0 | 7 | 33 | 27.300 | 27.300 | 79 |
| tranquillitatis_balmer_like_20km | sector-wave | 10 | OPTIMAL:10 | 4.977 | 1.749 | 10.951 | 26.743 | 0 | 3 | 15 | 12.200 | 12.200 | 81 |

## 最慢实例 Top 10

| rank | 地形 | 模式 | time | nodes | objective | pricing | exact pricing | columns | instance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | tranquillitatis_balmer_like_20km | random-wave | 52.723 | 29 | 338.615584 | 110 | 110 | 103 | `tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks010_06_seed51521` |
| 2 | tranquillitatis_balmer_like_20km | random-wave | 47.644 | 33 | 339.286391 | 113 | 113 | 88 | `tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks010_04_seed51316` |
| 3 | tranquillitatis_balmer_like_20km | greedy-anchor | 34.696 | 21 | 330.360353 | 79 | 79 | 100 | `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks010_10_seed51929` |
| 4 | tranquillitatis_balmer_like_20km | sector-wave | 26.743 | 15 | 352.168131 | 52 | 52 | 90 | `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_09_seed51864` |
| 5 | tranquillitatis_balmer_like_20km | greedy-anchor | 17.917 | 13 | 350.738862 | 53 | 53 | 93 | `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks010_08_seed51725` |
| 6 | tranquillitatis_balmer_like_20km | greedy-anchor | 11.503 | 7 | 343.508861 | 30 | 30 | 98 | `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks010_03_seed51213` |
| 7 | tranquillitatis_balmer_like_20km | sector-wave | 9.197 | 7 | 340.345242 | 28 | 28 | 63 | `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_05_seed51425` |
| 8 | apollo15_20km | greedy-anchor | 6.636 | 5 | 398.824764 | 20 | 20 | 67 | `apollo15_20km_greedy-anchor_randomtw_tasks010_04_seed51317` |
| 9 | tranquillitatis_balmer_like_20km | greedy-anchor | 4.515 | 3 | 347.471528 | 11 | 11 | 87 | `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks010_02_seed51111` |
| 10 | apollo15_20km | random-wave | 3.208 | 3 | 443.950073 | 10 | 10 | 25 | `apollo15_20km_random-wave_randomtw_tasks010_05_seed51431` |

## 节点数最高 Top 10

| rank | 地形 | 模式 | nodes | time | objective | pricing | exact pricing | columns | instance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | tranquillitatis_balmer_like_20km | random-wave | 33 | 47.644 | 339.286391 | 113 | 113 | 88 | `tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks010_04_seed51316` |
| 2 | tranquillitatis_balmer_like_20km | random-wave | 29 | 52.723 | 338.615584 | 110 | 110 | 103 | `tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks010_06_seed51521` |
| 3 | tranquillitatis_balmer_like_20km | greedy-anchor | 21 | 34.696 | 330.360353 | 79 | 79 | 100 | `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks010_10_seed51929` |
| 4 | tranquillitatis_balmer_like_20km | sector-wave | 15 | 26.743 | 352.168131 | 52 | 52 | 90 | `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_09_seed51864` |
| 5 | tranquillitatis_balmer_like_20km | greedy-anchor | 13 | 17.917 | 350.738862 | 53 | 53 | 93 | `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks010_08_seed51725` |
| 6 | tranquillitatis_balmer_like_20km | greedy-anchor | 7 | 11.503 | 343.508861 | 30 | 30 | 98 | `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks010_03_seed51213` |
| 7 | tranquillitatis_balmer_like_20km | sector-wave | 7 | 9.197 | 340.345242 | 28 | 28 | 63 | `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_05_seed51425` |
| 8 | apollo15_20km | greedy-anchor | 5 | 6.636 | 398.824764 | 20 | 20 | 67 | `apollo15_20km_greedy-anchor_randomtw_tasks010_04_seed51317` |
| 9 | tranquillitatis_balmer_like_20km | greedy-anchor | 3 | 4.515 | 347.471528 | 11 | 11 | 87 | `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks010_02_seed51111` |
| 10 | apollo15_20km | random-wave | 3 | 3.208 | 443.950073 | 10 | 10 | 25 | `apollo15_20km_random-wave_randomtw_tasks010_05_seed51431` |

## 逐实例结果

| 地形 | 模式 | # | 状态 | time | objective | nodes | pricing | exact pricing | columns | instance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| apollo15_20km | greedy-anchor | 1 | OPTIMAL | 1.862 | 410.506626 | 1 | 7 | 7 | 78 | `apollo15_20km_greedy-anchor_randomtw_tasks010_01_seed51001` |
| apollo15_20km | greedy-anchor | 2 | OPTIMAL | 1.602 | 416.400267 | 1 | 4 | 4 | 56 | `apollo15_20km_greedy-anchor_randomtw_tasks010_02_seed51106` |
| apollo15_20km | greedy-anchor | 3 | OPTIMAL | 1.898 | 300.567939 | 1 | 5 | 5 | 77 | `apollo15_20km_greedy-anchor_randomtw_tasks010_03_seed51209` |
| apollo15_20km | greedy-anchor | 4 | OPTIMAL | 6.636 | 398.824764 | 5 | 20 | 20 | 67 | `apollo15_20km_greedy-anchor_randomtw_tasks010_04_seed51317` |
| apollo15_20km | greedy-anchor | 5 | OPTIMAL | 1.701 | 400.620556 | 1 | 4 | 4 | 36 | `apollo15_20km_greedy-anchor_randomtw_tasks010_05_seed51431` |
| apollo15_20km | greedy-anchor | 6 | OPTIMAL | 1.487 | 437.316371 | 1 | 4 | 4 | 28 | `apollo15_20km_greedy-anchor_randomtw_tasks010_06_seed51534` |
| apollo15_20km | greedy-anchor | 7 | OPTIMAL | 1.490 | 403.177569 | 1 | 4 | 4 | 52 | `apollo15_20km_greedy-anchor_randomtw_tasks010_07_seed51656` |
| apollo15_20km | greedy-anchor | 8 | OPTIMAL | 1.564 | 471.328288 | 1 | 4 | 4 | 42 | `apollo15_20km_greedy-anchor_randomtw_tasks010_08_seed51771` |
| apollo15_20km | greedy-anchor | 9 | OPTIMAL | 1.702 | 332.696642 | 1 | 6 | 6 | 60 | `apollo15_20km_greedy-anchor_randomtw_tasks010_09_seed51914` |
| apollo15_20km | greedy-anchor | 10 | OPTIMAL | 1.703 | 392.818051 | 1 | 4 | 4 | 41 | `apollo15_20km_greedy-anchor_randomtw_tasks010_10_seed52016` |
| apollo15_20km | random-wave | 1 | OPTIMAL | 1.528 | 402.009327 | 1 | 4 | 4 | 50 | `apollo15_20km_random-wave_randomtw_tasks010_01_seed51001` |
| apollo15_20km | random-wave | 2 | OPTIMAL | 1.456 | 466.566544 | 1 | 5 | 5 | 31 | `apollo15_20km_random-wave_randomtw_tasks010_02_seed51106` |
| apollo15_20km | random-wave | 3 | OPTIMAL | 1.769 | 350.018272 | 1 | 5 | 5 | 52 | `apollo15_20km_random-wave_randomtw_tasks010_03_seed51209` |
| apollo15_20km | random-wave | 4 | OPTIMAL | 1.456 | 446.842799 | 1 | 4 | 4 | 37 | `apollo15_20km_random-wave_randomtw_tasks010_04_seed51317` |
| apollo15_20km | random-wave | 5 | OPTIMAL | 3.208 | 443.950073 | 3 | 10 | 10 | 25 | `apollo15_20km_random-wave_randomtw_tasks010_05_seed51431` |
| apollo15_20km | random-wave | 6 | OPTIMAL | 1.349 | 536.031264 | 1 | 3 | 3 | 20 | `apollo15_20km_random-wave_randomtw_tasks010_06_seed51534` |
| apollo15_20km | random-wave | 7 | OPTIMAL | 1.425 | 456.463793 | 1 | 5 | 5 | 32 | `apollo15_20km_random-wave_randomtw_tasks010_07_seed51656` |
| apollo15_20km | random-wave | 8 | OPTIMAL | 1.456 | 412.557404 | 1 | 4 | 4 | 37 | `apollo15_20km_random-wave_randomtw_tasks010_08_seed51771` |
| apollo15_20km | random-wave | 9 | OPTIMAL | 1.475 | 406.795536 | 1 | 4 | 4 | 46 | `apollo15_20km_random-wave_randomtw_tasks010_09_seed51914` |
| apollo15_20km | random-wave | 10 | OPTIMAL | 1.460 | 487.516589 | 1 | 4 | 4 | 30 | `apollo15_20km_random-wave_randomtw_tasks010_10_seed52016` |
| apollo15_20km | sector-wave | 1 | OPTIMAL | 2.909 | 456.756326 | 3 | 11 | 11 | 42 | `apollo15_20km_sector-wave_randomtw_tasks010_01_seed51001` |
| apollo15_20km | sector-wave | 2 | OPTIMAL | 1.359 | 515.223089 | 1 | 3 | 3 | 31 | `apollo15_20km_sector-wave_randomtw_tasks010_02_seed51106` |
| apollo15_20km | sector-wave | 3 | OPTIMAL | 1.539 | 416.518192 | 1 | 4 | 4 | 56 | `apollo15_20km_sector-wave_randomtw_tasks010_03_seed51209` |
| apollo15_20km | sector-wave | 4 | OPTIMAL | 1.705 | 419.729194 | 1 | 5 | 5 | 60 | `apollo15_20km_sector-wave_randomtw_tasks010_04_seed51343` |
| apollo15_20km | sector-wave | 5 | OPTIMAL | 1.508 | 460.203732 | 1 | 4 | 4 | 30 | `apollo15_20km_sector-wave_randomtw_tasks010_05_seed51448` |
| apollo15_20km | sector-wave | 6 | OPTIMAL | 1.504 | 458.391944 | 1 | 4 | 4 | 41 | `apollo15_20km_sector-wave_randomtw_tasks010_06_seed51552` |
| apollo15_20km | sector-wave | 7 | OPTIMAL | 1.424 | 384.405437 | 1 | 4 | 4 | 45 | `apollo15_20km_sector-wave_randomtw_tasks010_07_seed51656` |
| apollo15_20km | sector-wave | 8 | OPTIMAL | 1.563 | 409.029425 | 1 | 4 | 4 | 51 | `apollo15_20km_sector-wave_randomtw_tasks010_08_seed51771` |
| apollo15_20km | sector-wave | 9 | OPTIMAL | 1.435 | 402.607829 | 1 | 5 | 5 | 49 | `apollo15_20km_sector-wave_randomtw_tasks010_09_seed51914` |
| apollo15_20km | sector-wave | 10 | OPTIMAL | 1.543 | 436.113785 | 1 | 5 | 5 | 46 | `apollo15_20km_sector-wave_randomtw_tasks010_10_seed52016` |
| tranquillitatis_balmer_like_20km | greedy-anchor | 1 | OPTIMAL | 3.060 | 281.036362 | 1 | 8 | 8 | 111 | `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks010_01_seed51000` |
| tranquillitatis_balmer_like_20km | greedy-anchor | 2 | OPTIMAL | 4.515 | 347.471528 | 3 | 11 | 11 | 87 | `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks010_02_seed51111` |
| tranquillitatis_balmer_like_20km | greedy-anchor | 3 | OPTIMAL | 11.503 | 343.508861 | 7 | 30 | 30 | 98 | `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks010_03_seed51213` |
| tranquillitatis_balmer_like_20km | greedy-anchor | 4 | OPTIMAL | 1.782 | 284.146889 | 1 | 7 | 7 | 102 | `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks010_04_seed51316` |
| tranquillitatis_balmer_like_20km | greedy-anchor | 5 | OPTIMAL | 2.415 | 269.713621 | 1 | 11 | 11 | 111 | `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks010_05_seed51418` |
| tranquillitatis_balmer_like_20km | greedy-anchor | 6 | OPTIMAL | 2.469 | 334.121579 | 1 | 11 | 11 | 99 | `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks010_06_seed51521` |
| tranquillitatis_balmer_like_20km | greedy-anchor | 7 | OPTIMAL | 2.173 | 341.162735 | 1 | 7 | 7 | 95 | `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks010_07_seed51623` |
| tranquillitatis_balmer_like_20km | greedy-anchor | 8 | OPTIMAL | 17.917 | 350.738862 | 13 | 53 | 53 | 93 | `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks010_08_seed51725` |
| tranquillitatis_balmer_like_20km | greedy-anchor | 9 | OPTIMAL | 1.751 | 279.834594 | 1 | 6 | 6 | 90 | `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks010_09_seed51827` |
| tranquillitatis_balmer_like_20km | greedy-anchor | 10 | OPTIMAL | 34.696 | 330.360353 | 21 | 79 | 79 | 100 | `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks010_10_seed51929` |
| tranquillitatis_balmer_like_20km | random-wave | 1 | OPTIMAL | 2.400 | 334.943677 | 1 | 9 | 9 | 89 | `tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks010_01_seed51000` |
| tranquillitatis_balmer_like_20km | random-wave | 2 | OPTIMAL | 1.723 | 350.123158 | 1 | 5 | 5 | 82 | `tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks010_02_seed51111` |
| tranquillitatis_balmer_like_20km | random-wave | 3 | OPTIMAL | 1.552 | 359.110917 | 1 | 5 | 5 | 69 | `tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks010_03_seed51213` |
| tranquillitatis_balmer_like_20km | random-wave | 4 | OPTIMAL | 47.644 | 339.286391 | 33 | 113 | 113 | 88 | `tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks010_04_seed51316` |
| tranquillitatis_balmer_like_20km | random-wave | 5 | OPTIMAL | 1.700 | 286.695263 | 1 | 5 | 5 | 86 | `tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks010_05_seed51418` |
| tranquillitatis_balmer_like_20km | random-wave | 6 | OPTIMAL | 52.723 | 338.615584 | 29 | 110 | 110 | 103 | `tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks010_06_seed51521` |
| tranquillitatis_balmer_like_20km | random-wave | 7 | OPTIMAL | 1.720 | 356.007533 | 1 | 5 | 5 | 84 | `tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks010_07_seed51623` |
| tranquillitatis_balmer_like_20km | random-wave | 8 | OPTIMAL | 2.055 | 349.869195 | 1 | 9 | 9 | 72 | `tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks010_08_seed51725` |
| tranquillitatis_balmer_like_20km | random-wave | 9 | OPTIMAL | 1.517 | 342.675153 | 1 | 4 | 4 | 51 | `tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks010_09_seed51827` |
| tranquillitatis_balmer_like_20km | random-wave | 10 | OPTIMAL | 2.037 | 345.720918 | 1 | 8 | 8 | 66 | `tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks010_10_seed51929` |
| tranquillitatis_balmer_like_20km | sector-wave | 1 | OPTIMAL | 1.587 | 330.363821 | 1 | 4 | 4 | 71 | `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_01_seed51001` |
| tranquillitatis_balmer_like_20km | sector-wave | 2 | OPTIMAL | 2.099 | 350.404223 | 1 | 9 | 9 | 64 | `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_02_seed51116` |
| tranquillitatis_balmer_like_20km | sector-wave | 3 | OPTIMAL | 1.882 | 343.795018 | 1 | 4 | 4 | 100 | `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_03_seed51220` |
| tranquillitatis_balmer_like_20km | sector-wave | 4 | OPTIMAL | 1.682 | 266.869677 | 1 | 5 | 5 | 89 | `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_04_seed51323` |
| tranquillitatis_balmer_like_20km | sector-wave | 5 | OPTIMAL | 9.197 | 340.345242 | 7 | 28 | 28 | 63 | `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_05_seed51425` |
| tranquillitatis_balmer_like_20km | sector-wave | 6 | OPTIMAL | 1.755 | 350.957359 | 1 | 6 | 6 | 104 | `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_06_seed51549` |
| tranquillitatis_balmer_like_20km | sector-wave | 7 | OPTIMAL | 1.444 | 350.691562 | 1 | 4 | 4 | 76 | `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_07_seed51652` |
| tranquillitatis_balmer_like_20km | sector-wave | 8 | OPTIMAL | 1.744 | 414.963853 | 1 | 5 | 5 | 78 | `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_08_seed51762` |
| tranquillitatis_balmer_like_20km | sector-wave | 9 | OPTIMAL | 26.743 | 352.168131 | 15 | 52 | 52 | 90 | `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_09_seed51864` |
| tranquillitatis_balmer_like_20km | sector-wave | 10 | OPTIMAL | 1.637 | 384.705638 | 1 | 5 | 5 | 75 | `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_10_seed51969` |

## 结论

- 这批 10规模随机时间窗实例在 no-GNN baseline 下全部精确求得最优，且没有一个超过 60s；当前最慢为 `tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks010_06_seed51521`，52.723s。
- 性能瓶颈不是 Apollo 地形，而是 Tranquillitatis 地形中少数需要分支的实例；最重的几个实例节点数为 21、29、33。
- 由于所有实例都在 60s 内解决，这批 10规模数据适合作为“约束有效但不过紧”的训练/评测集；它已经不复现旧 tranq10_09 那种 root-tail final judge 长证明问题。
- no-GNN 覆盖生效：运行日志中未发现 learning/GNN 事件。
