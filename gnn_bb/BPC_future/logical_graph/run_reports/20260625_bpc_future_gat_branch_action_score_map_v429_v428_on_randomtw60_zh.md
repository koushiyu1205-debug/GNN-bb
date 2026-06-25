# GAT Branch/Action Score Map

日期：2026-06-26

## 目的

用已训练的 branch/action GAT checkpoint 对既有 `journey_branch_candidates` 日志离线打分，导出 solver 可 opt-in 读取的 branch score rows。

## 机器字段

```text
checkpoint = BPC_future/data/gat_branch_action_sanity/v427_v421_plus_v426_walltime_gain_20260625/gat_branch_action_v428_walltime_gain.pt
resolved_log_file_count = 60
score_row_count = 9258
score_instance_count = 39
solver_score_path = BPC_future/results/gat_branch_action_score_map_v429_v428_on_randomtw60_20260625/journey_branch_score_rows.json
score_min = 0.5318185091018677
score_max = 0.9364717602729797
score_mean = 0.6995337616099372
skipped_counts = {}
runs_bpc_or_pricing = False
official_bound_effect = False
certificate_effect = False
pricing_oracle = False
branching_oracle = False
production_ready = False
```

## Top Rows

- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=2 depth=1 pair=[5, 12] score=0.936472
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=2 depth=1 pair=[6, 12] score=0.935944
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=2 depth=1 pair=[5, 20] score=0.935399
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=2 depth=1 pair=[9, 12] score=0.935120
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=2 depth=1 pair=[12, 20] score=0.934960
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=2 depth=1 pair=[4, 12] score=0.934288
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=2 depth=1 pair=[3, 12] score=0.932676
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=2 depth=1 pair=[5, 6] score=0.932206
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=2 depth=1 pair=[6, 9] score=0.931896
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=2 depth=1 pair=[4, 5] score=0.931812
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=2 depth=1 pair=[9, 20] score=0.930599
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=2 depth=1 pair=[4, 9] score=0.930239

## 使用边界

`solver_score_path` 应作为 `journey_branch_candidate_score_path` 使用；不要使用无上下文聚合 map 作为生产配置。
这些分数只改变 opt-in 的 Ryan-Foster pair 排序；所有下界、剪枝和 OPTIMAL 证书仍由 exact pricing / BPC 逻辑产生。
