# GAT Branch Action v432 Selection-Gate Smoke

日期：2026-06-26

## 结论

- v432 是 normal branch score selection gate 的安全壳验证，不是最终加速版本。
- 12 个 20-scale top-score smoke：OPTIMAL 2/12，TIME_LIMIT 1/12，EXTERNAL_TIME_LIMIT 9/12。
- capped mean：v432 = 513.51s，canonical baseline = 535.69s，v430 full-open = 496.92s。
- v432 保住了 `seed61001` 的强加速：327.7s OPTIMAL -> 59.2s OPTIMAL。
- v432 修掉了 v430 的两个明显退化：`seed61846` 回到 145.7s OPTIMAL，`seed61414` 回到 baseline 水平的内部 TIME_LIMIT。
- v432 也拦掉了 `seed61744` 的非最优快速收益：v430 293.9s TIME_LIMIT，v432 回到 600s EXTERNAL。这个收益不能直接当 production positive，因为没有最优证书。

## 机器字段

```text
run_dir = BPC_future/results/20260626_v432_branch_score_selection_gate_smoke20_topscore12
config_delta = branch_score_horizon + selection_gate(min_score=0.67,total_width<=700,balance<=100,max_child_width<=380), admission=off, early_branch=off
status_counts = {'EXTERNAL_TIME_LIMIT': 9, 'TIME_LIMIT': 1, 'OPTIMAL': 2}
v432_capped_mean = 513.507786
baseline_capped_mean = 535.692741
v430_capped_mean = 496.919228
gate_reason_counts = {'pool_total_width_exceeds_cap': 3, 'missing_score_source': 187, 'ok': 1, 'score_below_min': 8}
changed_branch_event_count = 1
early_branch_trigger_count = 0
non_exact_child_count = 0
```

## 实例对比

- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json`: v432=EXTERNAL_TIME_LIMIT 600.0s, baseline=EXTERNAL_TIME_LIMIT 600.0s, v430=TIME_LIMIT 293.9s, gain_vs_base=0.0s, gain_vs_v430=-306.1s, root [1, 4] -> [1, 4], changed=False, score=0.709966296, gate=pool_total_width_exceeds_cap, max_node=12, branches=8, fathom=0
- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json`: v432=EXTERNAL_TIME_LIMIT 600.0s, baseline=EXTERNAL_TIME_LIMIT 600.0s, v430=EXTERNAL_TIME_LIMIT 600.0s, gain_vs_base=0.0s, gain_vs_v430=0.0s, root [5, 9] -> [5, 9], changed=False, score=0.680870473, gate=pool_total_width_exceeds_cap, max_node=36, branches=20, fathom=0
- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json`: v432=TIME_LIMIT 557.2s, baseline=TIME_LIMIT 555.7s, v430=EXTERNAL_TIME_LIMIT 600.0s, gain_vs_base=-1.4s, gain_vs_v430=42.8s, root [13, 16] -> [13, 16], changed=False, score=0.679828203, gate=pool_total_width_exceeds_cap, max_node=12, branches=6, fathom=6
- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json`: v432=OPTIMAL 59.2s, baseline=OPTIMAL 327.7s, v430=OPTIMAL 60.6s, gain_vs_base=268.5s, gain_vs_v430=1.4s, root [2, 18] -> [3, 12], changed=True, score=0.671353847, gate=ok, max_node=2, branches=1, fathom=2
- `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_10_seed61923_logical_graph.json`: v432=EXTERNAL_TIME_LIMIT 600.0s, baseline=EXTERNAL_TIME_LIMIT 600.0s, v430=EXTERNAL_TIME_LIMIT 600.0s, gain_vs_base=0.0s, gain_vs_v430=0.0s, root [1, 13] -> [1, 13], changed=False, score=0.661020619, gate=score_below_min, max_node=24, branches=14, fathom=0
- `apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json`: v432=EXTERNAL_TIME_LIMIT 600.0s, baseline=EXTERNAL_TIME_LIMIT 600.0s, v430=EXTERNAL_TIME_LIMIT 600.0s, gain_vs_base=0.0s, gain_vs_v430=0.0s, root [1, 2] -> [1, 2], changed=False, score=0.64278025, gate=score_below_min, max_node=26, branches=13, fathom=5
- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json`: v432=OPTIMAL 145.7s, baseline=OPTIMAL 144.8s, v430=OPTIMAL 208.4s, gain_vs_base=-0.9s, gain_vs_v430=62.7s, root [2, 5] -> [2, 5], changed=False, score=0.663038045, gate=score_below_min, max_node=6, branches=3, fathom=4
- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json`: v432=EXTERNAL_TIME_LIMIT 600.0s, baseline=EXTERNAL_TIME_LIMIT 600.0s, v430=EXTERNAL_TIME_LIMIT 600.0s, gain_vs_base=0.0s, gain_vs_v430=0.0s, root [4, 7] -> [4, 7], changed=False, score=0.653063476, gate=score_below_min, max_node=52, branches=30, fathom=0
- `tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json`: v432=EXTERNAL_TIME_LIMIT 600.0s, baseline=EXTERNAL_TIME_LIMIT 600.0s, v430=EXTERNAL_TIME_LIMIT 600.0s, gain_vs_base=0.0s, gain_vs_v430=0.0s, root [1, 9] -> [1, 9], changed=False, score=0.653948188, gate=score_below_min, max_node=68, branches=34, fathom=16
- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json`: v432=EXTERNAL_TIME_LIMIT 600.0s, baseline=EXTERNAL_TIME_LIMIT 600.0s, v430=EXTERNAL_TIME_LIMIT 600.0s, gain_vs_base=0.0s, gain_vs_v430=0.0s, root [10, 15] -> [10, 15], changed=False, score=0.616847271, gate=score_below_min, max_node=18, branches=9, fathom=7
- `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json`: v432=EXTERNAL_TIME_LIMIT 600.0s, baseline=EXTERNAL_TIME_LIMIT 600.0s, v430=EXTERNAL_TIME_LIMIT 600.0s, gain_vs_base=0.0s, gain_vs_v430=0.0s, root [5, 14] -> [5, 14], changed=False, score=0.624273944, gate=score_below_min, max_node=54, branches=35, fathom=0
- `tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json`: v432=EXTERNAL_TIME_LIMIT 600.0s, baseline=EXTERNAL_TIME_LIMIT 600.0s, v430=EXTERNAL_TIME_LIMIT 600.0s, gain_vs_base=0.0s, gain_vs_v430=0.0s, root [8, 13] -> [8, 13], changed=False, score=0.631337106, gate=score_below_min, max_node=50, branches=26, fathom=19

## 判断

- selection gate 是必要的：它把 branch score 从 full-open 改成低风险 opt-in，能避免 score precision 不足造成的退化。
- 但当前 gate 太保守，不能提升 OPTIMAL 数；它只吃到一个已知强正例。
- v430 比 v432 capped mean 更低，是因为 v430 接受了 `seed61744` 这种未证明最优的快速 TIME_LIMIT 路径；这对平均 capped wall time 有帮助，但不满足 20-scale 600s 全最优目标。
- 当前真正瓶颈仍在 child proof tail：多数实例回退 baseline 后还是 600s 外部超时。

## 下一步

- 保留 v432 selection gate 作为 branch-score 安全壳；不要回到 full-open。
- 已导出 depth 0/1、top200 的 score map：`BPC_future/results/gat_branch_action_v430_randomtw60_20260626/score_map_v421_depth01_top200_hybrid/journey_branch_score_rows.json`。
- 对 v432 smoke 的 branch-candidate 事件做离线覆盖检查：旧 root/top50 map 总候选命中率 6.6%，新 depth0/1/top200 map 总候选命中率 14.1%；depth1 命中率从 0% 提升到 75.9%。depth2+ 仍为 0%，所以它只能改善第一层 child context，不解决深树 proof tail。
- 把 `seed61744` 标成 speed-positive-but-uncertified，只用于 proof-cost/ranking 辅助，不作为 production strong positive。
- 下一轮训练要提高 hard negative / regression 权重，尤其是高分但 child tree 变宽的样本。
- 要达成 20 全部 600s OPTIMAL，还必须继续攻 proof tail：branch score 只能减少坏分支，不能单独证明所有 child。
