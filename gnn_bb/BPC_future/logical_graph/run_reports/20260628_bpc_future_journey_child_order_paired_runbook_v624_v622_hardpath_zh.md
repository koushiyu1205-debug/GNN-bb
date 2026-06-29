# Journey Child Order Paired Replay Runbook

该 runbook 只从已有 JSONL 日志抽取 hard-path branch 节点并生成 same-first / separate-first 成对 replay 命令；生成本身不运行 BPC / pricing / RMP。

## Summary

- source_log_count: `4`
- source_branch_event_count: `158`
- selected_pair_count: `4`
- entry_count: `8`
- time_limit: `220`
- probe_extra_nodes_after_branch: `4`
- probe_max_cg_iterations: `18`

## Entries

### 001_child_order_same_vehicle_d1_n2_13_20_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph

- instance: `BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json`
- source depth/node: `1` / `2`
- source pair: `[13, 20]`
- target_child_kind: `same_vehicle`
- source_first_child_kind: `same_vehicle`
- priority_score: `357.0`
- subtree CB retry: `54`
- forced_pair_path_rule: `force_pair_path:0:14,19=separate_vehicle;1:13,20`
- forced_child_kind_depth_rule: `force_child_kind_depth:0:separate_vehicle;1:same_vehicle`

### 002_child_order_separate_vehicle_d1_n2_13_20_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph

- instance: `BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json`
- source depth/node: `1` / `2`
- source pair: `[13, 20]`
- target_child_kind: `separate_vehicle`
- source_first_child_kind: `same_vehicle`
- priority_score: `357.0`
- subtree CB retry: `54`
- forced_pair_path_rule: `force_pair_path:0:14,19=separate_vehicle;1:13,20`
- forced_child_kind_depth_rule: `force_child_kind_depth:0:separate_vehicle;1:separate_vehicle`

### 003_child_order_same_vehicle_d1_n2_16_19_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph

- instance: `BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json`
- source depth/node: `1` / `2`
- source pair: `[16, 19]`
- target_child_kind: `same_vehicle`
- source_first_child_kind: `same_vehicle`
- priority_score: `284.0`
- subtree CB retry: `41`
- forced_pair_path_rule: `force_pair_path:0:11,17=separate_vehicle;1:16,19`
- forced_child_kind_depth_rule: `force_child_kind_depth:0:separate_vehicle;1:same_vehicle`

### 004_child_order_separate_vehicle_d1_n2_16_19_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph

- instance: `BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json`
- source depth/node: `1` / `2`
- source pair: `[16, 19]`
- target_child_kind: `separate_vehicle`
- source_first_child_kind: `same_vehicle`
- priority_score: `284.0`
- subtree CB retry: `41`
- forced_pair_path_rule: `force_pair_path:0:11,17=separate_vehicle;1:16,19`
- forced_child_kind_depth_rule: `force_child_kind_depth:0:separate_vehicle;1:separate_vehicle`

### 005_child_order_same_vehicle_d1_n1_16_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

- instance: `BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json`
- source depth/node: `1` / `1`
- source pair: `[16, 20]`
- target_child_kind: `same_vehicle`
- source_first_child_kind: `same_vehicle`
- priority_score: `167.0`
- subtree CB retry: `25`
- forced_pair_path_rule: `force_pair_path:0:17,20=same_vehicle;1:16,20`
- forced_child_kind_depth_rule: `force_child_kind_depth:0:same_vehicle;1:same_vehicle`

### 006_child_order_separate_vehicle_d1_n1_16_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

- instance: `BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json`
- source depth/node: `1` / `1`
- source pair: `[16, 20]`
- target_child_kind: `separate_vehicle`
- source_first_child_kind: `same_vehicle`
- priority_score: `167.0`
- subtree CB retry: `25`
- forced_pair_path_rule: `force_pair_path:0:17,20=same_vehicle;1:16,20`
- forced_child_kind_depth_rule: `force_child_kind_depth:0:same_vehicle;1:separate_vehicle`

### 007_child_order_same_vehicle_d1_n2_13_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph

- instance: `BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json`
- source depth/node: `1` / `2`
- source pair: `[13, 20]`
- target_child_kind: `same_vehicle`
- source_first_child_kind: `same_vehicle`
- priority_score: `134.0`
- subtree CB retry: `19`
- forced_pair_path_rule: `force_pair_path:0:15,18=separate_vehicle;1:13,20`
- forced_child_kind_depth_rule: `force_child_kind_depth:0:separate_vehicle;1:same_vehicle`

### 008_child_order_separate_vehicle_d1_n2_13_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph

- instance: `BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json`
- source depth/node: `1` / `2`
- source pair: `[13, 20]`
- target_child_kind: `separate_vehicle`
- source_first_child_kind: `same_vehicle`
- priority_score: `134.0`
- subtree CB retry: `19`
- forced_pair_path_rule: `force_pair_path:0:15,18=separate_vehicle;1:13,20`
- forced_child_kind_depth_rule: `force_child_kind_depth:0:separate_vehicle;1:separate_vehicle`

## Paired Replay Result

原始 runbook 的 8 条命令已执行。seed61635 在 `max_cg_iterations=18` 时没有到达目标 branch，后续单独补跑：

- output: `BPC_future/results/journey_child_order_paired_runbook_v624b_seed61635_cg48_20260628/`
- time_limit: `300`
- max_cg_iterations / journey_max_cg_iterations: `48`

补跑后 seed61635 两条均到达目标 branch `[13,20]`，并且 forced child order 生效。

| seed | pair | same-first wall | separate-first wall | separate - same | same CB retry | separate CB retry | gap | target branch |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| 61718 | [13,20] | 52.316s | 51.222s | -1.094s | 6 | 6 | 0.050472 | reached |
| 61410 | [16,19] | 95.709s | 82.659s | -13.051s | 7 | 6 | 0.034203 | reached |
| 61311 | [16,20] | 101.255s | 103.261s | +2.005s | 6 | 6 | 0.051947 | reached |
| 61635 | [13,20] | 106.833s | 106.739s | -0.094s | 6 | 6 | 0.061278 | reached |

所有 paired replay 都是固定预算 probe，因此 `TIME_LIMIT` 本身不是失败标签；这里关注的是同一实例、同一路径、同一父分支、不同 child first order 下的局部 proof-cost 差异。

## Label Usability

- 可用弱正例：seed61410 / pair `[16,19]`，`separate_vehicle` first 比 `same_vehicle` first 快约 `13.05s`，并少 1 次 completion-bound/final-judge retry。
- 中性样本：seed61718、seed61635，wall 差异小于 2 秒且 CB retry 相同。
- 弱负例：seed61311 / pair `[16,20]`，`separate_vehicle` first 慢约 `2.01s`，CB retry 相同。

当前还不能把这批数据作为主训练集，因为：

1. paired 数量只有 4 组；
2. 唯一明显信号仍只是固定预算局部 probe，不是完整 600s full-solve wall-time closure；
3. child-order 影响弱于 branch-pair 选择影响，大部分 hard case 的瓶颈仍是后续树宽和 completion-bound/final-judge proof tail。

但这批结果证明了一个重要方向：相比直接从 full-open 结果里猜因果，paired replay 可以在相同父 branch 上制造严格可比的 child-order 反事实。下一步应扩大到更多 hard-path branch 节点，并记录：

- target branch 是否到达；
- forced child order 是否生效；
- child first order 对 wall、CB retry、fathom count、gap progress 的影响；
- 若 probe 未闭环，至少保留 exact-safe gap。

## Current Interpretation

V624 没有直接带来 20 规模求解加速，它的产出是训练数据生成能力。

目前更清楚的结论是：

- retry gate 不是主加速器，只能减少一部分昂贵 completion-bound/final-judge retry；过早 gate 会让 fathom 事件减少、树变宽。
- child ordering 有局部信号，但目前信号偏弱，不能指望只调 same/separate 顺序解决 600s timeout。
- branch pair 选择仍是主线；child ordering 应作为 branch score 的辅助 head 或 tie-breaker，而不是单独主控策略。
- 后续数据采集要从“完整实例是否进 200s”改成多层标签：full-solve wall-time gain、hard-path branch-pair replay、child-order paired proof-cost、gap progress。这样没有 OPTIMAL 的实例也能贡献可训练信号，但不能把它们当成 strict full-solve positive。
