# Journey Child Order Paired Summary

该报告汇总 same-first / separate-first paired replay 的局部 proof-cost 差异；它只读已有结果和 JSONL 日志，不运行 BPC / pricing / RMP，不产生 official bound 或 certificate。

## Summary

- entry_count: `8`
- candidate_run_count: `10`
- paired_group_count: `4`
- valid_paired_group_count: `4`
- label_counts: `{'hard_negative_child_order_proxy': 1, 'neutral_child_order_proxy': 6, 'positive_child_order_proxy': 1}`
- rows: `BPC_future/results/journey_child_order_paired_summary_v629_v624_hardpath_queuefix_20260628/child_order_paired_rows.jsonl`
- groups: `BPC_future/results/journey_child_order_paired_summary_v629_v624_hardpath_queuefix_20260628/child_order_paired_group_rows.jsonl`

## Groups

### tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d1__n1__16_20

- instance: `BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json`
- depth / pair: `1` / `[16, 20]`
- same-first wall: `101.255484`
- separate-first wall: `103.260724`
- separate - same wall: `2.00524`
- same / separate CB retry: `6` / `6`
- preferred_child_kind: `neutral`
- target branch reached: `True` / `True`
- forced order effective: `True` / `True`

### tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph__d1__n2__13_20

- instance: `BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json`
- depth / pair: `1` / `[13, 20]`
- same-first wall: `106.833316`
- separate-first wall: `106.738886`
- separate - same wall: `-0.09443`
- same / separate CB retry: `6` / `6`
- preferred_child_kind: `neutral`
- target branch reached: `True` / `True`
- forced order effective: `True` / `True`

### tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph__d1__n2__16_19

- instance: `BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json`
- depth / pair: `1` / `[16, 19]`
- same-first wall: `95.709344`
- separate-first wall: `82.658671`
- separate - same wall: `-13.050673`
- same / separate CB retry: `7` / `6`
- preferred_child_kind: `separate_vehicle`
- target branch reached: `True` / `True`
- forced order effective: `True` / `True`

### tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph__d1__n2__13_20

- instance: `BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json`
- depth / pair: `1` / `[13, 20]`
- same-first wall: `52.3156`
- separate-first wall: `51.221854`
- separate - same wall: `-1.093746`
- same / separate CB retry: `6` / `6`
- preferred_child_kind: `neutral`
- target branch reached: `True` / `True`
- forced order effective: `True` / `True`

## Interpretation

这些 rows 是 child-order 的弱监督/诊断标签。正值 wall gain 表示当前 child kind 比 opposite child kind 更快；gap improvement 只来自 solver/result 或 exact-safe 日志字段，不使用未闭合 RMP objective。

