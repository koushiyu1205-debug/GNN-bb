# V543 Branch + Tree Policy Merged Overlay

日期：2026-06-27

## 目的

合并 V467 当前 best conservative root overlay 与 V540 state-rehydrated tree overlay，避免用 V540 替换 V467 后丢掉已验证 root 正例。

## 机器字段

```text
input_paths = ['BPC_future/results/gat_branch_action_v466_weighted_walltime_20260627/score_map_v467_conservative_overlay_on_branchonly60/journey_branch_score_rows.json', 'BPC_future/results/gat_tree_policy_strict_overlay_v540_v537_plus_v529_state_rehydrated_20260627/journey_branch_score_rows.json']
score_row_count = 20768
score_max = 0.91
score_ge_067_count = 44
score_ge_085_count = 30
recommended_min_score = 0.67
recommended_require_state_key = True
production_ready = False
official_bound_effect = False
certificate_effect = False
```

## 使用边界

该 score map 只改变 Ryan-Foster branch ordering；不提供 official bound、certificate 或剪枝依据。
使用时应设置 `journey_branch_candidate_score_require_state_key=True`，并把 selection gate min score 设置为 `0.67`。
