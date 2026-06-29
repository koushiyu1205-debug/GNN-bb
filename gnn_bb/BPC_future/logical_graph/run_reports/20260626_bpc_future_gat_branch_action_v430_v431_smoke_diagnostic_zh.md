# GAT Branch Action v430/v431 Smoke Diagnostic

日期：2026-06-26

## 结论

- v430/v431 这一轮实现完成了 branch decision 字段、wall-time gain 训练头、score map 导出、score-gated early branch，以及新增的 normal branch score selection gate。
- 12-instance 20 规模 smoke 没有通过：OPTIMAL 2/12，TIME_LIMIT 1/12，EXTERNAL_TIME_LIMIT 9/12，capped mean 496.9s。不能扩到 full 60。
- 但 smoke 证明 branch score 有真实信号：`seed61001` 从 canonical baseline 327.7s OPTIMAL 降到 60.6s OPTIMAL。
- 同时也证明当前 score map precision 不够：多个高分 root pair 导致外部超时或 OPTIMAL 退化。
- score-gated early branch 本轮没有真正触发；当前实际起作用的是 normal Ryan-Foster branch score 排序。

## v430 Score Map

```text
score_instance_count = 41
score_row_count = 1581
score_min/mean/max = 0.36739524900913234 / 0.5840927210715962 / 0.7135628640651702
solver_score_path = BPC_future/results/gat_branch_action_v430_randomtw60_20260626/score_map_v421_root_top50_hybrid/journey_branch_score_rows.json
```

## Smoke 结果

```text
result_dir = BPC_future/results/20260626_v430_score_gated_early_branch_smoke20_topscore12
status_counts = {'TIME_LIMIT': 1, 'EXTERNAL_TIME_LIMIT': 9, 'OPTIMAL': 2}
capped_mean = 496.919228
OPTIMAL_only_mean = 134.543404
le200_OPTIMAL = 1
win_gt30_vs_canonical = 2
loss_gt30_vs_canonical = 2
early_branch_trigger_count = 0
```

## 实例明细

- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json`: smoke=TIME_LIMIT 293.9s, baseline=EXTERNAL_TIME_LIMIT 600.0s, gain=306.1s, root [1, 4] -> [2, 19], score=0.713562864, max_node=2, branches=1, fathom=0
- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json`: smoke=EXTERNAL_TIME_LIMIT 600.0s, baseline=EXTERNAL_TIME_LIMIT 600.0s, gain=0.0s, root [5, 9] -> [1, 6], score=0.689357311, max_node=30, branches=18, fathom=0
- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json`: smoke=EXTERNAL_TIME_LIMIT 600.0s, baseline=TIME_LIMIT 555.7s, gain=-44.3s, root [13, 16] -> [1, 12], score=0.68582589, max_node=18, branches=9, fathom=6
- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json`: smoke=OPTIMAL 60.6s, baseline=OPTIMAL 327.7s, gain=267.1s, root [2, 18] -> [3, 12], score=0.671353847, max_node=2, branches=1, fathom=2
- `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_10_seed61923_logical_graph.json`: smoke=EXTERNAL_TIME_LIMIT 600.0s, baseline=EXTERNAL_TIME_LIMIT 600.0s, gain=0.0s, root [1, 13] -> [2, 11], score=0.666820174, max_node=18, branches=11, fathom=1
- `apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json`: smoke=EXTERNAL_TIME_LIMIT 600.0s, baseline=EXTERNAL_TIME_LIMIT 600.0s, gain=0.0s, root [1, 2] -> [4, 16], score=0.664579332, max_node=22, branches=15, fathom=5
- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json`: smoke=OPTIMAL 208.4s, baseline=OPTIMAL 144.8s, gain=-63.6s, root [2, 5] -> [2, 16], score=0.66322999, max_node=10, branches=5, fathom=6
- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json`: smoke=EXTERNAL_TIME_LIMIT 600.0s, baseline=EXTERNAL_TIME_LIMIT 600.0s, gain=0.0s, root [4, 7] -> [6, 11], score=0.655632728, max_node=42, branches=28, fathom=0
- `tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json`: smoke=EXTERNAL_TIME_LIMIT 600.0s, baseline=EXTERNAL_TIME_LIMIT 600.0s, gain=0.0s, root [1, 9] -> [1, 12], score=0.65441196, max_node=66, branches=33, fathom=18
- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json`: smoke=EXTERNAL_TIME_LIMIT 600.0s, baseline=EXTERNAL_TIME_LIMIT 600.0s, gain=0.0s, root [10, 15] -> [1, 4], score=0.639845496, max_node=20, branches=13, fathom=4
- `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json`: smoke=EXTERNAL_TIME_LIMIT 600.0s, baseline=EXTERNAL_TIME_LIMIT 600.0s, gain=0.0s, root [5, 14] -> [1, 2], score=0.639368826, max_node=73, branches=38, fathom=0
- `tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json`: smoke=EXTERNAL_TIME_LIMIT 600.0s, baseline=EXTERNAL_TIME_LIMIT 600.0s, gain=0.0s, root [8, 13] -> [8, 19], score=0.636823797, max_node=52, branches=33, fathom=17

## 训练结果

```text
v430_dataset: raw_rows=193, samples=114, branch_priority_labels={'walltime_gain_positive': 51, 'not_walltime_gain': 54, 'aux_only_weak_positive': 9}
v430_validation: precision=0.2962962962962963, recall=1.0, f1=0.45714285714285713, mean_score=0.6680622012526901
v431_dataset: raw_rows=205, samples=116, branch_priority_labels={'aux_only_weak_positive': 9, 'not_walltime_gain': 55, 'walltime_gain_positive': 52}
v431_validation: precision=0.2857142857142857, recall=1.0, f1=0.4444444444444445, mean_score=0.8802371514695031
```

## 为什么会这样

- `branch_score_horizon` 只要有 score 就会改变正常 branch；原来的 score gate 只限制 early branch，限制不到正常 branch 排序。
- v430 score map 主要覆盖 root，child context 大量缺失。root pair 改对时很快闭环，改错时子节点继续按 fractionality 分支，树会迅速变宽。
- 当前模型 recall 高但 precision 低，validation 上几乎把大多数候选都判成正向；这解释了为什么有真实加速，也有明显退化。
- `seed61744` 说明只看分数还不够：score=0.713，但 pool_total_child_width=1172，超出 early-branch cap，最终只得到 TIME_LIMIT 而非 OPTIMAL。
- 追加 12 个 smoke rows 后 v431 validation precision 反而略低，说明样本量太小，不能靠一次重训修正。

## 已完成的修正

- 新增 normal branch score selection gate，默认关闭。启用后 score 候选必须满足 source、min_score、pool_total_child_width、pool_balance_gap、pool_max_child_width，否则回退 fractionality。
- `journey_branch_candidates` / `journey_branch` 会记录 `branch_score_selection_gate_enabled/pass/reason`。
- 新增单测：高分 pair 超 width cap 时 `_choose_journey_branch` 回退 baseline pair。
- 生成 v431 smoke replay rows：`BPC_future/results/journey_branch_counterfactual_delta_v431_v430_score_gated_smoke20_20260626/branch_counterfactual_delta_rows.jsonl`。

## 下一步

- 不扩 v430/v431 到 full 60。先用 selection gate 跑一个小 smoke：normal branch score 只在 `score/source/width` 都通过时生效。
- score map 导出不应只用 root/top50；要增加 child context 覆盖，至少导出 depth 0/1 的 top200。
- 训练标签继续使用 capped wall-time gain，但 hard negative 要提高权重，尤其是 OPTIMAL 变慢和高分改 pair 后树宽变大的样本。
- early branch 仍保持 opt-in；在 normal branch score precision 稳定前，不让它承担主加速路径。

