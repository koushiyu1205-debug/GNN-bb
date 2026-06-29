# Journey Child Order Paired Summary

该报告汇总 same-first / separate-first paired replay 的局部 proof-cost 差异；它只读已有结果和 JSONL 日志，不运行 BPC / pricing / RMP，不产生 official bound 或 certificate。

## Summary

- entry_count: `24`
- candidate_run_count: `24`
- paired_group_count: `12`
- valid_paired_group_count: `9`
- label_counts: `{'hard_negative_child_order_proxy': 4, 'invalid_unreached': 5, 'neutral_child_order_proxy': 13, 'positive_child_order_proxy': 2}`
- rows: `BPC_future/results/journey_child_order_paired_summary_v628_v626_hardpath12_queuefix_20260628/child_order_paired_rows.jsonl`
- groups: `BPC_future/results/journey_child_order_paired_summary_v628_v626_hardpath12_queuefix_20260628/child_order_paired_group_rows.jsonl`

## Groups

### tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d1__n1__16_20

- instance: `BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json`
- depth / pair: `1` / `[16, 20]`
- same-first wall: `118.759055`
- separate-first wall: `121.312393`
- separate - same wall: `2.553338`
- same / separate CB retry: `7` / `7`
- preferred_child_kind: `neutral`
- target branch reached: `True` / `True`
- forced order effective: `True` / `True`

### tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d2__n3__15_17

- instance: `BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json`
- depth / pair: `2` / `[15, 17]`
- same-first wall: `140.677121`
- separate-first wall: `128.463535`
- separate - same wall: `-12.213586`
- same / separate CB retry: `9` / `8`
- preferred_child_kind: `separate_vehicle`
- target branch reached: `True` / `True`
- forced order effective: `True` / `True`

### tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d3__n7__1_9

- instance: `BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json`
- depth / pair: `3` / `[1, 9]`
- same-first wall: `140.594285`
- separate-first wall: `140.677121`
- separate - same wall: `0.082836`
- same / separate CB retry: `9` / `9`
- preferred_child_kind: `neutral`
- target branch reached: `True` / `True`
- forced order effective: `True` / `False`

### tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph__d1__n1__16_18

- instance: `BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json`
- depth / pair: `1` / `[16, 18]`
- same-first wall: `106.728707`
- separate-first wall: `106.590363`
- separate - same wall: `-0.138344`
- same / separate CB retry: `7` / `7`
- preferred_child_kind: `neutral`
- target branch reached: `True` / `True`
- forced order effective: `True` / `True`

### tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph__d1__n2__13_20

- instance: `BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json`
- depth / pair: `1` / `[13, 20]`
- same-first wall: `116.729088`
- separate-first wall: `117.021253`
- separate - same wall: `0.292165`
- same / separate CB retry: `7` / `7`
- preferred_child_kind: `neutral`
- target branch reached: `True` / `True`
- forced order effective: `True` / `True`

### tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph__d2__n6__11_18

- instance: `BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json`
- depth / pair: `2` / `[11, 18]`
- same-first wall: `133.890566`
- separate-first wall: `133.767944`
- separate - same wall: `-0.122622`
- same / separate CB retry: `8` / `8`
- preferred_child_kind: `neutral`
- target branch reached: `True` / `True`
- forced order effective: `True` / `True`

### tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph__d1__n2__16_19

- instance: `BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json`
- depth / pair: `1` / `[16, 19]`
- same-first wall: `108.131986`
- separate-first wall: `90.982526`
- separate - same wall: `-17.14946`
- same / separate CB retry: `8` / `7`
- preferred_child_kind: `separate_vehicle`
- target branch reached: `True` / `True`
- forced order effective: `True` / `True`

### tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph__d2__n6__14_16

- instance: `BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json`
- depth / pair: `2` / `[14, 16]`
- same-first wall: `129.153343`
- separate-first wall: `129.795244`
- separate - same wall: `0.641901`
- same / separate CB retry: `10` / `10`
- preferred_child_kind: `neutral`
- target branch reached: `False` / `False`
- forced order effective: `False` / `False`

### tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph__d3__n10__1_9

- instance: `BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json`
- depth / pair: `3` / `[1, 9]`
- same-first wall: `129.153343`
- separate-first wall: `129.795244`
- separate - same wall: `0.641901`
- same / separate CB retry: `10` / `10`
- preferred_child_kind: `neutral`
- target branch reached: `False` / `False`
- forced order effective: `False` / `False`

### tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph__d1__n2__13_20

- instance: `BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json`
- depth / pair: `1` / `[13, 20]`
- same-first wall: `59.109583`
- separate-first wall: `59.664056`
- separate - same wall: `0.554473`
- same / separate CB retry: `7` / `7`
- preferred_child_kind: `neutral`
- target branch reached: `True` / `True`
- forced order effective: `True` / `True`

### tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph__d2__n6__11_20

- instance: `BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json`
- depth / pair: `2` / `[11, 20]`
- same-first wall: `76.237457`
- separate-first wall: `66.877561`
- separate - same wall: `-9.359896`
- same / separate CB retry: `8` / `8`
- preferred_child_kind: `separate_vehicle`
- target branch reached: `True` / `True`
- forced order effective: `True` / `True`

### tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph__d3__n14__2_6

- instance: `BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json`
- depth / pair: `3` / `[2, 6]`
- same-first wall: `82.630278`
- separate-first wall: `82.723259`
- separate - same wall: `0.092981`
- same / separate CB retry: `9` / `9`
- preferred_child_kind: `neutral`
- target branch reached: `True` / `True`
- forced order effective: `True` / `True`

## Interpretation

这些 rows 是 child-order 的弱监督/诊断标签。正值 wall gain 表示当前 child kind 比 opposite child kind 更快；gap improvement 只来自 solver/result 或 exact-safe 日志字段，不使用未闭合 RMP objective。

## V628 结论

这批 V626 replay 的主要价值不是直接产生一个可上线的 child-score map，而是把 child-order 反事实标签的边界看清楚了。

- `12` 个 paired group 中，`9` 个通过 queued-order 审计，`3` 个不适合作为 child-order 标签。
- 标签行分布：`2` positive、`4` hard negative、`13` neutral、`5` invalid。
- 有稳定正信号的两组都是 `separate_vehicle` first：
  - greedy-anchor seed61311 / depth 2 / pair `[15,17]`：约 `12.21s` gain，少 1 次 completion-bound/final-judge retry。
  - sector-wave seed61410 / depth 1 / pair `[16,19]`：约 `17.15s` gain，少 1 次 completion-bound/final-judge retry。
- sector-wave seed61718 / depth 2 / pair `[11,20]` 是反例：`separate_vehicle` first 更快约 `9.36s`，但 gap 变差，因此不能当正例。
- 多数组仍然 neutral，说明 child ordering 的收益是局部的，不能替代 branch pair selection。

## 对主线的影响

1. child-order 可以作为 branch score 的辅助/tie-breaker，不应作为主加速策略。
2. replay 采样必须把 `target_branch_seen` 和 `forced_child_order_effective` 作为硬过滤条件。
3. depth 越深越容易出现 force path 没到目标或 force-child-depth 没命中预期父节点；后续优先采 depth 1-2，再少量补 depth 3。
4. 训练时不能只看 wall gain，还要同时看 gap improvement；更快但 gap 变差的样本应进 hard negative 或至少不进 positive。
5. 当前 20 规模 600s timeout 的主因仍是 branch pair / subtree proof tail，而不是 same/separate 子节点入队顺序。

下一步更应该扩展 branch-pair paired replay 和 full-solve wall-time delta；child-order rows 只作为辅助标签进入 tree-policy/GAT 的 child-order head。
