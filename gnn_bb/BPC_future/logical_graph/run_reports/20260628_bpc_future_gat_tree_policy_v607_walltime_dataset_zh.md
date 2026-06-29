# GAT Tree-Policy Event Dataset

日期：2026-06-28

## 目的

把 tree-policy event rows 转成 GAT graph samples。默认只训练 tree_policy 辅助 head；显式 include_walltime_labels 时，带 capped wall-time gain 的严格 replay row 也会训练 branch-priority / wall-time head。

## 机器字段

```text
sample_count = 981
include_walltime_labels = True
branch_priority_label_counts = {'walltime_gain_positive': 31, 'aux_only_tree_policy': 946, 'not_walltime_gain': 4}
tree_policy_label_counts = {'tree_policy_positive': 31, 'tree_policy_hard_negative': 936, 'tree_policy_proof_tail_hard_negative': 14}
target_wall_crossing_label_counts = {'not_target_wall_crossing': 981}
tail_improved_aux_label_counts = {'tail_improved': 31, 'tail_not_improved': 950}
instance_counts = {'BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json': 438, 'BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json': 410, 'BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json': 5, 'BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json': 4, 'BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json': 80, 'BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json': 8, 'BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json': 22, 'BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json': 14}
skipped_counts = {'missing_instance_file': 5}
runs_bpc_or_pricing = false
official_bound_effect = false
certificate_effect = false
production_ready = false
```

## 边界

该数据集不能单独证明模型可泛化；它只生成离线训练样本，不运行 BPC/pricing/RMP，也不影响 official bound、certificate 或剪枝。wall-time 标签仅来自已完成 strict replay / controlled replay 的观测字段。
