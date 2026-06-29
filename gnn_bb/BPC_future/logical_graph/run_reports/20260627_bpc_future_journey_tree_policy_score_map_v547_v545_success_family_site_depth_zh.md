# Journey Tree Policy Score Map

日期：2026-06-27

## 目的

从多个成功日志聚合 branch pair 和 child ordering 偏好，生成 opt-in tree-policy score map。该脚本只读日志，不运行 BPC / pricing / RMP，不产生 official bound 或 certificate。

## 机器字段

```text
input_log_count = 36
parsed_log_count = 36
branch_score_row_count = 124
child_score_row_count = 248
skipped_branch_event_count = 0
skipped_child_event_count = 0
key_scope = depth
context_scope = family_site
solver_branch_priority = branch_score_horizon
solver_child_priority_mode = child_score
branch_score_rows_path = BPC_future/results/journey_tree_policy_score_map_v547_v545_success_family_site_depth_20260627/journey_branch_tree_policy_score_rows.json
child_score_rows_path = BPC_future/results/journey_tree_policy_score_map_v547_v545_success_family_site_depth_20260627/journey_child_tree_policy_score_rows.json
production_ready = False
certificate_effect = False
official_bound_effect = False
```

## Top Branch Rows

- scope=greedy-anchor/apollo15_20km depth=0 pair=[4, 12] score=999.795213662 obs=1
- scope=greedy-anchor/apollo15_20km depth=0 pair=[4, 19] score=999.729070772 obs=1
- scope=greedy-anchor/apollo15_20km depth=0 pair=[12, 20] score=999.590284876 obs=1
- scope=greedy-anchor/apollo15_20km depth=1 pair=[4, 6] score=999.75287906 obs=1
- scope=greedy-anchor/apollo15_20km depth=1 pair=[1, 2] score=999.660139946 obs=1
- scope=greedy-anchor/apollo15_20km depth=1 pair=[2, 10] score=999.432732131 obs=1
- scope=greedy-anchor/apollo15_20km depth=2 pair=[1, 4] score=999.513925741 obs=1
- scope=greedy-anchor/tranquillitatis_balmer_like_20km depth=0 pair=[3, 4] score=999.82482523 obs=1
- scope=greedy-anchor/tranquillitatis_balmer_like_20km depth=0 pair=[6, 15] score=999.814092874 obs=1
- scope=greedy-anchor/tranquillitatis_balmer_like_20km depth=0 pair=[2, 5] score=999.78106617 obs=1
- scope=greedy-anchor/tranquillitatis_balmer_like_20km depth=0 pair=[6, 20] score=999.739625341 obs=1
- scope=greedy-anchor/tranquillitatis_balmer_like_20km depth=1 pair=[1, 12] score=999.73259726 obs=1
- scope=greedy-anchor/tranquillitatis_balmer_like_20km depth=1 pair=[2, 17] score=999.729044443 obs=1
- scope=greedy-anchor/tranquillitatis_balmer_like_20km depth=1 pair=[3, 17] score=999.679826736 obs=1
- scope=greedy-anchor/tranquillitatis_balmer_like_20km depth=1 pair=[1, 4] score=999.67929376 obs=1
- scope=greedy-anchor/tranquillitatis_balmer_like_20km depth=2 pair=[1, 2] score=999.578409865 obs=1

## Top Child Rows

- scope=greedy-anchor/apollo15_20km depth=0 pair=[4, 12] kind=same_vehicle score=999.8 obs=1
- scope=greedy-anchor/apollo15_20km depth=0 pair=[4, 12] kind=separate_vehicle score=899.799 obs=1
- scope=greedy-anchor/apollo15_20km depth=0 pair=[4, 19] kind=same_vehicle score=999.736 obs=1
- scope=greedy-anchor/apollo15_20km depth=0 pair=[4, 19] kind=separate_vehicle score=899.735 obs=1
- scope=greedy-anchor/apollo15_20km depth=0 pair=[12, 20] kind=same_vehicle score=999.6 obs=1
- scope=greedy-anchor/apollo15_20km depth=0 pair=[12, 20] kind=separate_vehicle score=899.599 obs=1
- scope=greedy-anchor/apollo15_20km depth=1 pair=[1, 2] kind=same_vehicle score=999.672 obs=1
- scope=greedy-anchor/apollo15_20km depth=1 pair=[1, 2] kind=separate_vehicle score=899.671 obs=1
- scope=greedy-anchor/apollo15_20km depth=1 pair=[2, 10] kind=same_vehicle score=999.455 obs=1
- scope=greedy-anchor/apollo15_20km depth=1 pair=[2, 10] kind=separate_vehicle score=899.454 obs=1
- scope=greedy-anchor/apollo15_20km depth=1 pair=[4, 6] kind=same_vehicle score=999.763 obs=1
- scope=greedy-anchor/apollo15_20km depth=1 pair=[4, 6] kind=separate_vehicle score=899.762 obs=1
- scope=greedy-anchor/apollo15_20km depth=2 pair=[1, 4] kind=same_vehicle score=999.54 obs=1
- scope=greedy-anchor/apollo15_20km depth=2 pair=[1, 4] kind=separate_vehicle score=899.539 obs=1
- scope=greedy-anchor/tranquillitatis_balmer_like_20km depth=0 pair=[2, 5] kind=same_vehicle score=999.783 obs=1
- scope=greedy-anchor/tranquillitatis_balmer_like_20km depth=0 pair=[2, 5] kind=separate_vehicle score=899.782 obs=1

## 使用边界

`branch_score_horizon` 和 `child_score` 只改变排序/入队顺序；不提供 bound，不剪枝，不替代 exact pricing closure。
该 map 是跨实例聚合启发式，必须经过 smoke/full replay 才能进入 production-ready 训练或默认配置。
