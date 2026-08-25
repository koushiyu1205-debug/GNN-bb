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

- model: `P0V4_BIDIRECTIONAL_SRI_GROUP_SCREEN_ALL_SCALE_CANDIDATE_V5_S30_native_rcspp_bidirectional_root_partial_hybrid_v3`
- config hash: `dab1cb143c280072`
- root engine: `b2b_r3_worker`
- worker pricer: `relaxed_labeling`, max task cap `30`
- labeling harvest: support-aware `True`, weak replacement cap `8`, support overlap `0.6`
- labeling support-continuation: enabled `True`, max seed sets `240`, max neighbors `4`, protected `8`
- large-task direct worker: enabled `False`, max tasks `12`, candidate sets `240`, time cap `25.0`
- labeling final judge: `on`, max exact tasks `30`, exact harvest target `64`
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
- root-pool post-final-judge selected/new/replacement/added: `26012` / `25999` / `13` / `26012`
- root-partition post-final feedback selected/added: `0` / `0`
- all redlines zero: `True`
- accepted: `False`

| scale | rows | exact | under300 exact | fail-closed | mean total | max total | mean root | mean partition | mean tree |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 30 | 20 | 20 | 17 | 0 | 140.842145 | 836.065307 | 84.164613 | None | 55.894124 |

## Per-Instance

| scale | instance | status | scope | pricing | exact | under300 | total | root | partition | tree | active cols | exact harvest | worker harvest | post-FJ added | post-partition added | terminal | provenance | fail reason |
|---:|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 30 | instance_001 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 63.646376 | 50.578729 | None | 12.259753 | 1583 | 0 | 0 | 1549 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_002 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 22.352916 | 18.355165 | None | 3.277437 | 1198 | 0 | 0 | 1166 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_003 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 33.032919 | 25.728961 | None | 6.566232 | 1098 | 0 | 0 | 1064 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_004 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 29.576538 | 16.46538 | None | 12.366778 | 1358 | 0 | 0 | 1324 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_005 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 22.852229 | 12.689504 | None | 9.447875 | 1058 | 0 | 0 | 1024 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_006 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 18.379439 | 13.376433 | None | 4.299551 | 985 | 0 | 0 | 953 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_007 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 63.201331 | 38.271139 | None | 24.193452 | 1308 | 0 | 0 | 1275 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_008 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 44.68184 | 24.457535 | None | 19.389558 | 1442 | 0 | 0 | 1408 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_009 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | False | 836.065307 | 566.543981 | None | 268.689805 | 1353 | 0 | 0 | 1320 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_010 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | False | 398.028782 | 202.575165 | None | 194.596106 | 1469 | 0 | 0 | 1435 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_011 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 53.726287 | 39.037431 | None | 13.889787 | 1254 | 0 | 0 | 1221 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_012 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | False | 499.468499 | 368.264168 | None | 130.276601 | 2075 | 0 | 0 | 2042 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_013 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 108.61513 | 56.548413 | None | 51.284866 | 1370 | 0 | 0 | 1339 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_014 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 105.905146 | 86.596964 | None | 18.514213 | 1348 | 0 | 0 | 1314 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_015 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 27.71583 | 18.666144 | None | 8.298335 | 1183 | 0 | 0 | 1149 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_016 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 31.223578 | 17.405742 | None | 13.057448 | 1256 | 0 | 0 | 1223 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_017 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 30.377695 | 23.687918 | None | 5.934924 | 1099 | 0 | 0 | 1065 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_018 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 223.764832 | 37.63621 | None | 185.350399 | 1235 | 0 | 0 | 1201 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_019 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 170.961899 | 37.377624 | None | 132.800126 | 1233 | 0 | 0 | 1199 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_020 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 33.266327 | 29.029648 | None | 3.389238 | 1774 | 0 | 0 | 1741 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
