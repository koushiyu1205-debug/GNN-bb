# GAT Tree-Policy Event Dataset

日期：2026-06-27

## 目的

把 tree-policy event rows 转成 GAT graph samples。该 dataset 只训练 tree_policy 辅助 head，legacy branch-priority/wall-time loss 权重为 0。

## 机器字段

```text
sample_count = 966
tree_policy_label_counts = {'tree_policy_positive': 29, 'tree_policy_hard_negative': 937}
instance_counts = {'BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json': 438, 'BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json': 410, 'BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json': 5, 'BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json': 4, 'BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json': 79, 'BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json': 8, 'BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json': 22}
skipped_counts = {}
runs_bpc_or_pricing = false
official_bound_effect = false
certificate_effect = false
production_ready = false
```

## 边界

该数据集不能单独证明模型可泛化；当前正例来自 2 个完整成功实例，仍只能用于辅助头 sanity/ablation。
