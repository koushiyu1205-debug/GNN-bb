# Journey Child Order Paired Summary

该报告汇总 same-first / separate-first paired replay 的局部 proof-cost 差异；它只读已有结果和 JSONL 日志，不运行 BPC / pricing / RMP，不产生 official bound 或 certificate。

## Summary

- entry_count: `24`
- candidate_run_count: `24`
- paired_group_count: `12`
- valid_paired_group_count: `6`
- label_counts: `{'hard_negative_child_order_proxy': 3, 'invalid_unreached': 12, 'neutral_child_order_proxy': 8, 'positive_child_order_proxy': 1}`
- rows: `BPC_future/results/journey_child_order_paired_summary_v627_v626_hardpath12_20260628/child_order_paired_rows.jsonl`
- groups: `BPC_future/results/journey_child_order_paired_summary_v627_v626_hardpath12_20260628/child_order_paired_group_rows.jsonl`

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
- same-first wall: `140.594285`
- separate-first wall: `140.677121`
- separate - same wall: `0.082836`
- same / separate CB retry: `9` / `9`
- preferred_child_kind: `neutral`
- target branch reached: `True` / `True`
- forced order effective: `False` / `False`

### tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d3__n7__1_9

- instance: `BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json`
- depth / pair: `3` / `[1, 9]`
- same-first wall: `140.594285`
- separate-first wall: `140.677121`
- separate - same wall: `0.082836`
- same / separate CB retry: `9` / `9`
- preferred_child_kind: `neutral`
- target branch reached: `True` / `True`
- forced order effective: `False` / `False`

### tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph__d1__n1__16_18

- instance: `BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json`
- depth / pair: `1` / `[16, 18]`
- same-first wall: `106.728707`
- separate-first wall: `106.590363`
- separate - same wall: `-0.138344`
- same / separate CB retry: `7` / `7`
- preferred_child_kind: `neutral`
- target branch reached: `True` / `True`
- forced order effective: `False` / `False`

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
- forced order effective: `False` / `False`

## Interpretation

这些 rows 是 child-order 的弱监督/诊断标签。正值 wall gain 表示当前 child kind 比 opposite child kind 更快；gap improvement 只来自 solver/result 或 exact-safe 日志字段，不使用未闭合 RMP objective。

