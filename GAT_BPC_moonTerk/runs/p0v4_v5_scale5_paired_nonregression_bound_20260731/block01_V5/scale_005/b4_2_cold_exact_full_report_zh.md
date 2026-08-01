# B4.2 Cold-Start Exact 300s Report

## 边界

- 正式行必须从 `instance_XXX_logical_graph.json` 冷启动。
- 禁止外部 mature probe、同实例历史列池、手工补列、按实例调参。
- 同一次 run 内 staged checkpoint 可以续跑，但所有 stage 时间计入 `cold_start_total_sec`。
- `BPC_TREE_OPTIMAL` 只证明 normalized additive objective，不证明 makespan-in-objective。
- B4.2 V1 固定 seed 为 B0 incumbent + singleton，并启用固定 route-template pre-harvest worker；worker 只找列，不给 no-negative 证书。
- root pool 使用固定 `b2b_r3_worker`，默认 worker 为 `relaxed_labeling`；fixed worker max task cap 是全局 config/hash 字段，不允许按实例调参。
- tail dual stabilization 只作用于 worker candidate search。
- support-continuation seed 只基于当前 RMP support 自动生成 add/drop/swap 邻域列；只找列，不给 no-negative 证书。
- final judge 使用 `labeling_final_judge=auto`：5/10 默认走 exact labeling proof，超过 fixed max exact tasks 时自动回到 compact/exhaustive proof。

## 汇总

- model: `P0V4_BIDIRECTIONAL_SRI_GROUP_SCREEN_ALL_SCALE_CANDIDATE_V5_S5_native_rcspp_bidirectional_root_partial_hybrid_v3`
- config hash: `5e58bcf1f62b0df5`
- root engine: `b2b_r3_worker`
- worker pricer: `relaxed_labeling`, max task cap `5`
- labeling harvest: support-aware `True`, weak replacement cap `8`, support overlap `0.6`
- labeling support-continuation: enabled `True`, max seed sets `240`, max neighbors `4`, protected `8`
- large-task direct worker: enabled `False`, max tasks `12`, candidate sets `240`, time cap `25.0`
- labeling final judge: `on`, max exact tasks `5`, exact harvest target `8`
- rows: `20`
- no-cheat fail: `0`
- worker certificate leaks: `0`
- tail-dual certificate leaks: `0`
- true-dual RC recompute missing: `0`
- root-pool worker/tail-dual/redline counts: `0` / `0` / `0`
- root-pool support-continuation seeds/active/protected/leaks: `0` / `0` / `0` / `0`
- root-pool large-task direct worker seeds/rounds/columns/true-negatives/leaks: `0` / `0` / `0` / `0` / `0`
- root-pool exact harvest candidates/selected/new/replacement: `0` / `0` / `0` / `0`
- root-pool worker selected/new/replacement: `0` / `0` / `0`
- root-pool post-final-judge selected/new/replacement/added: `360` / `340` / `20` / `360`
- root-partition post-final feedback selected/added: `0` / `0`
- all redlines zero: `True`
- accepted: `False`

| scale | rows | exact | under300 exact | fail-closed | mean total | max total | mean root | mean partition | mean tree |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 | 20 | 20 | 20 | 0 | 0.454543 | 0.503302 | 0.125515 | None | 0.186485 |

## Per-Instance

| scale | instance | status | scope | pricing | exact | under300 | total | root | partition | tree | active cols | exact harvest | worker harvest | post-FJ added | post-partition added | terminal | provenance | fail reason |
|---:|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 5 | instance_001 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.428513 | 0.114953 | None | 0.171033 | 22 | 0 | 0 | 17 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_002 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.424631 | 0.11994 | None | 0.1592 | 22 | 0 | 0 | 17 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_003 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.44041 | 0.118715 | None | 0.179967 | 26 | 0 | 0 | 21 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_004 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.4619 | 0.135362 | None | 0.185831 | 21 | 0 | 0 | 16 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_005 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.415501 | 0.115272 | None | 0.158924 | 21 | 0 | 0 | 16 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_006 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.453076 | 0.107147 | None | 0.206058 | 24 | 0 | 0 | 19 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_007 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.458863 | 0.118713 | None | 0.196808 | 21 | 0 | 0 | 16 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_008 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.48167 | 0.136305 | None | 0.201509 | 21 | 0 | 0 | 16 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_009 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.456929 | 0.12269 | None | 0.193208 | 27 | 0 | 0 | 22 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_010 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.503302 | 0.169171 | None | 0.189184 | 29 | 0 | 0 | 24 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_011 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.48428 | 0.131719 | None | 0.213712 | 17 | 0 | 0 | 12 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_012 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.44345 | 0.119245 | None | 0.181708 | 24 | 0 | 0 | 19 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_013 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.466941 | 0.124832 | None | 0.201052 | 21 | 0 | 0 | 16 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_014 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.440915 | 0.12257 | None | 0.177039 | 24 | 0 | 0 | 19 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_015 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.477837 | 0.127578 | None | 0.206514 | 27 | 0 | 0 | 22 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_016 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.457642 | 0.138619 | None | 0.175965 | 21 | 0 | 0 | 16 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_017 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.446449 | 0.121253 | None | 0.184908 | 13 | 0 | 0 | 8 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_018 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.471149 | 0.148841 | None | 0.174704 | 27 | 0 | 0 | 22 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_019 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.432318 | 0.11021 | None | 0.178754 | 25 | 0 | 0 | 20 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_020 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.445086 | 0.107155 | None | 0.193625 | 27 | 0 | 0 | 22 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
