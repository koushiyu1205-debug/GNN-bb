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

- model: `NATIVE_SPPRC_ACCEPTANCE_V1_S30_native_rcspp_inprocess`
- config hash: `e1e0cd13a1ba7dcd`
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
- root-pool post-final-judge selected/new/replacement/added: `39397` / `39300` / `97` / `39374`
- root-partition post-final feedback selected/added: `0` / `0`
- all redlines zero: `True`
- accepted: `False`

| scale | rows | exact | under300 exact | fail-closed | mean total | max total | mean root | mean partition | mean tree |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 30 | 20 | 20 | 17 | 0 | 151.2166 | 846.962641 | 84.74712 | None | 65.615056 |

## Per-Instance

| scale | instance | status | scope | pricing | exact | under300 | total | root | partition | tree | active cols | exact harvest | worker harvest | post-FJ added | post-partition added | terminal | provenance | fail reason |
|---:|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 30 | instance_001 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 105.631421 | 27.955656 | None | 76.858768 | 1872 | 0 | 0 | 1838 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_002 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 65.28311 | 53.506544 | None | 11.054098 | 1269 | 0 | 0 | 1237 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_003 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 42.842151 | 37.953271 | None | 4.112958 | 1825 | 0 | 0 | 1792 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_004 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 38.382932 | 33.321768 | None | 4.276563 | 1902 | 0 | 0 | 1868 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_005 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 169.37613 | 83.470856 | None | 85.101139 | 1754 | 0 | 0 | 1725 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_006 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 45.550201 | 39.577353 | None | 5.169759 | 1861 | 0 | 0 | 1828 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_007 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 42.420617 | 36.935023 | None | 4.738546 | 1666 | 0 | 0 | 1635 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_008 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 61.462563 | 44.144887 | None | 16.456615 | 2082 | 0 | 0 | 2048 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_009 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 194.909814 | 156.985845 | None | 37.056751 | 1994 | 0 | 0 | 1961 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_010 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 51.700813 | 38.204792 | None | 12.677329 | 1634 | 0 | 0 | 1600 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_011 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 49.009115 | 42.355861 | None | 5.840908 | 1897 | 0 | 0 | 1867 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_012 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | False | 345.14696 | 297.511361 | None | 46.743559 | 2158 | 0 | 0 | 2124 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_013 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | False | 312.541621 | 258.949269 | None | 52.674893 | 2351 | 0 | 0 | 2318 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_014 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 255.578877 | 189.873379 | None | 64.854835 | 1923 | 0 | 0 | 1889 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_015 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 31.201667 | 26.347609 | None | 3.964726 | 2308 | 0 | 0 | 2304 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_016 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | False | 846.962641 | 65.853965 | None | 780.138973 | 2463 | 0 | 0 | 2432 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_017 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 150.525828 | 71.881018 | None | 77.81301 | 1760 | 0 | 0 | 1734 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_018 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 52.682952 | 46.585724 | None | 5.227421 | 1910 | 0 | 0 | 1881 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_019 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 116.987778 | 103.407706 | None | 12.477168 | 3133 | 0 | 0 | 3108 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 30 | instance_020 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 46.134799 | 40.120521 | None | 5.0631 | 2218 | 0 | 0 | 2185 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
