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
- config hash: `089c80ab5d29032e`
- root engine: `b2b_r3_worker`
- worker pricer: `relaxed_labeling`, max task cap `30`
- labeling harvest: support-aware `True`, weak replacement cap `8`, support overlap `0.6`
- labeling support-continuation: enabled `True`, max seed sets `240`, max neighbors `4`, protected `8`
- large-task direct worker: enabled `False`, max tasks `12`, candidate sets `240`, time cap `25.0`
- labeling final judge: `on`, max exact tasks `30`, exact harvest target `64`
- rows: `17`
- no-cheat fail: `0`
- worker certificate leaks: `0`
- tail-dual certificate leaks: `0`
- true-dual RC recompute missing: `0`
- root-pool worker/tail-dual/redline counts: `0` / `0` / `0`
- root-pool support-continuation seeds/active/protected/leaks: `0` / `0` / `0` / `0`
- root-pool large-task direct worker seeds/rounds/columns/true-negatives/leaks: `0` / `0` / `0` / `0` / `0`
- root-pool exact harvest candidates/selected/new/replacement: `0` / `0` / `0` / `0`
- root-pool worker selected/new/replacement: `0` / `0` / `0`
- root-pool post-final-judge selected/new/replacement/added: `22202` / `22191` / `11` / `22202`
- root-partition post-final feedback selected/added: `0` / `0`
- all redlines zero: `True`
- accepted: `False`

| scale | rows | exact | under300 exact | fail-closed | mean total | max total | mean root | mean partition | mean tree |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 30 | 17 | 17 | 14 | 0 | 146.868916 | 845.833827 | 83.246917 | None | 62.811974 |

## Per-Instance

| scale | instance | status | scope | pricing | exact | under300 | total | root | partition | tree | active cols | exact harvest | worker harvest | post-FJ added | post-partition added | terminal | provenance | fail reason |
|---:|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 30 | instance_011 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 53.614045 | 38.974056 | None | 13.785197 | 1254 | 0 | 0 | 1221 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_015 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 25.949273 | 17.320677 | None | 7.88119 | 1183 | 0 | 0 | 1149 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_016 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 31.049263 | 17.305237 | None | 12.94916 | 1256 | 0 | 0 | 1223 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_008 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 44.826191 | 24.653866 | None | 19.324571 | 1442 | 0 | 0 | 1408 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_009 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | False | 845.833827 | 573.376004 | None | 271.634635 | 1353 | 0 | 0 | 1320 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_012 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | False | 354.689744 | 225.744876 | None | 128.035147 | 1809 | 0 | 0 | 1776 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_017 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 28.303802 | 22.181813 | None | 5.395526 | 1099 | 0 | 0 | 1065 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_010 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | False | 405.863128 | 204.253471 | None | 200.783491 | 1469 | 0 | 0 | 1435 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_020 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 31.877759 | 27.769481 | None | 3.228144 | 1774 | 0 | 0 | 1741 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_005 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 21.508027 | 11.878181 | None | 8.895403 | 1058 | 0 | 0 | 1024 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_001 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 64.335846 | 51.095881 | None | 12.359393 | 1583 | 0 | 0 | 1549 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_019 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 144.172907 | 37.356493 | None | 106.012322 | 1233 | 0 | 0 | 1199 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_004 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 29.806859 | 16.634436 | None | 12.383233 | 1358 | 0 | 0 | 1324 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_018 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 224.278515 | 38.034386 | None | 185.443029 | 1235 | 0 | 0 | 1201 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_007 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 61.413491 | 37.029836 | None | 23.599853 | 1308 | 0 | 0 | 1275 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_006 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 17.69797 | 12.995505 | None | 3.963316 | 985 | 0 | 0 | 953 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_013 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 111.550925 | 58.593387 | None | 52.129951 | 1370 | 0 | 0 | 1339 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
