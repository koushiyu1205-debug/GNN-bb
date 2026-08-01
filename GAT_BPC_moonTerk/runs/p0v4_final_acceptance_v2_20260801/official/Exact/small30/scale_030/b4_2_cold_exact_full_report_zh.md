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

- model: `P0V4_V5_BIDIRECTIONAL_EXACT_FINAL_CANDIDATE_S30_native_rcspp_bidirectional_root_partial_hybrid_v3`
- config hash: `d151e1f5a0203123`
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
| 30 | 20 | 20 | 20 | 0 | 80.853075 | 260.425934 | 48.905529 | None | 31.215269 |

## Per-Instance

| scale | instance | status | scope | pricing | exact | under300 | total | root | partition | tree | active cols | exact harvest | worker harvest | post-FJ added | post-partition added | terminal | provenance | fail reason |
|---:|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 30 | instance_001 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 73.006777 | 15.680423 | None | 56.662536 | 844 | 0 | 0 | 810 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_002 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 24.090458 | 12.598044 | None | 10.823902 | 866 | 0 | 0 | 833 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_003 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 11.620728 | 6.833595 | None | 4.105423 | 1060 | 0 | 0 | 1026 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_004 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 24.499626 | 19.504535 | None | 4.323809 | 906 | 0 | 0 | 873 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_005 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 222.309207 | 48.723179 | None | 172.81988 | 1274 | 0 | 0 | 1240 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_006 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 19.499582 | 13.33211 | None | 5.410862 | 1442 | 0 | 0 | 1408 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_007 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 14.778655 | 9.690174 | None | 4.440827 | 859 | 0 | 0 | 827 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_008 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 54.734576 | 36.574473 | None | 17.437385 | 1304 | 0 | 0 | 1270 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_009 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 100.464123 | 66.863883 | None | 32.870042 | 1157 | 0 | 0 | 1123 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_010 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 75.4083 | 62.061231 | None | 12.547042 | 1501 | 0 | 0 | 1467 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_011 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 30.517559 | 24.145456 | None | 5.65114 | 1216 | 0 | 0 | 1186 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_012 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 102.508564 | 68.517033 | None | 33.239567 | 1378 | 0 | 0 | 1344 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_013 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 260.425934 | 199.14807 | None | 60.565135 | 1146 | 0 | 0 | 1113 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_014 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 226.12438 | 132.94755 | None | 92.403763 | 1426 | 0 | 0 | 1392 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_015 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 16.383816 | 11.960036 | None | 3.71017 | 1168 | 0 | 0 | 1134 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_016 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 133.212691 | 70.598761 | None | 61.872874 | 1150 | 0 | 0 | 1116 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_017 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 50.037471 | 26.354013 | None | 22.942778 | 1188 | 0 | 0 | 1154 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_018 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 25.778378 | 19.953383 | None | 5.113428 | 1125 | 0 | 0 | 1092 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_019 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 111.39963 | 97.972178 | None | 12.518777 | 2023 | 0 | 0 | 1989 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_020 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 40.261041 | 34.652461 | None | 4.846043 | 1338 | 0 | 0 | 1304 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
