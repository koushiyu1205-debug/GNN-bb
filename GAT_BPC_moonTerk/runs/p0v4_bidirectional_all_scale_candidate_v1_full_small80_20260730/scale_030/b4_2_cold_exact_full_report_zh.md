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

- model: `P0V4_BIDIRECTIONAL_MIDPOINT_ALL_SCALE_CANDIDATE_V1_S30_native_rcspp_bidirectional_midpoint_hybrid_v1`
- config hash: `a01b0f8a0d1801b2`
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
- root-pool post-final-judge selected/new/replacement/added: `23701` / `23691` / `10` / `23701`
- root-partition post-final feedback selected/added: `0` / `0`
- all redlines zero: `True`
- accepted: `False`

| scale | rows | exact | under300 exact | fail-closed | mean total | max total | mean root | mean partition | mean tree |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 30 | 20 | 20 | 19 | 0 | 89.392668 | 371.001991 | 48.464859 | None | 40.204829 |

## Per-Instance

| scale | instance | status | scope | pricing | exact | under300 | total | root | partition | tree | active cols | exact harvest | worker harvest | post-FJ added | post-partition added | terminal | provenance | fail reason |
|---:|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 30 | instance_001 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 72.723724 | 15.471093 | None | 56.61212 | 844 | 0 | 0 | 810 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_002 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 23.99533 | 12.547987 | None | 10.794505 | 866 | 0 | 0 | 833 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_003 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 11.541835 | 6.792996 | None | 4.06763 | 1060 | 0 | 0 | 1026 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_004 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 24.379072 | 19.514511 | None | 4.218113 | 906 | 0 | 0 | 873 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_005 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 172.622307 | 48.52685 | None | 123.35321 | 1274 | 0 | 0 | 1240 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_006 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 19.565661 | 13.505506 | None | 5.302177 | 1442 | 0 | 0 | 1408 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_007 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 14.644756 | 9.635847 | None | 4.372453 | 859 | 0 | 0 | 827 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_008 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 54.42558 | 36.270762 | None | 17.429832 | 1304 | 0 | 0 | 1270 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_009 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 99.908898 | 66.925166 | None | 32.262909 | 1157 | 0 | 0 | 1123 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_010 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 74.623664 | 61.334122 | None | 12.50028 | 1501 | 0 | 0 | 1467 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_011 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 30.942492 | 24.567353 | None | 5.64727 | 1216 | 0 | 0 | 1186 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_012 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 101.067214 | 68.196735 | None | 32.125872 | 1378 | 0 | 0 | 1344 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_013 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 254.699546 | 196.540334 | None | 57.461989 | 1146 | 0 | 0 | 1113 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_014 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 219.122747 | 128.910195 | None | 89.448893 | 1426 | 0 | 0 | 1392 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_015 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 16.318986 | 11.927144 | None | 3.689577 | 1168 | 0 | 0 | 1134 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_016 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | False | 371.001991 | 70.322092 | None | 299.934456 | 1150 | 0 | 0 | 1116 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_017 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 49.597999 | 26.369699 | None | 22.510231 | 1188 | 0 | 0 | 1154 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_018 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 25.73092 | 19.886686 | None | 5.123038 | 1125 | 0 | 0 | 1092 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_019 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 110.893412 | 97.621446 | None | 12.380257 | 2023 | 0 | 0 | 1989 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_020 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 40.04722 | 34.430648 | None | 4.861771 | 1338 | 0 | 0 | 1304 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
