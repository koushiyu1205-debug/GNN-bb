# GAT Tree-Policy Event Dataset

日期：2026-06-28

## 目的

把 tree-policy event rows 转成 GAT graph samples。默认只训练 tree_policy 辅助 head；显式 include_walltime_labels 时，带 capped wall-time gain 的严格 replay row 也会训练 branch-priority / wall-time head。

## 机器字段

```text
sample_count = 166
include_walltime_labels = False
branch_priority_label_counts = {'aux_only_tree_policy': 166}
tree_policy_label_counts = {'tree_policy_proof_tail_hard_negative': 166}
target_wall_crossing_label_counts = {'not_target_wall_crossing': 166}
tail_improved_aux_label_counts = {'tail_not_improved': 166}
instance_counts = {'BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json': 34, 'BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json': 31, 'BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json': 40, 'BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json': 61}
skipped_counts = {}
runs_bpc_or_pricing = false
official_bound_effect = false
certificate_effect = false
production_ready = false
```

## 边界

该数据集不能单独证明模型可泛化；它只生成离线训练样本，不运行 BPC/pricing/RMP，也不影响 official bound、certificate 或剪枝。wall-time 标签仅来自已完成 strict replay / controlled replay 的观测字段。
