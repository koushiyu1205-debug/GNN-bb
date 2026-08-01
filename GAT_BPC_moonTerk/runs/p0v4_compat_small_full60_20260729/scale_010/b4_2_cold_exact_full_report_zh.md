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

- model: `NATIVE_SPPRC_ACCEPTANCE_V1_S10_native_rcspp_inprocess`
- config hash: `5c44e0f4a53390a9`
- root engine: `b2b_r3_worker`
- worker pricer: `relaxed_labeling`, max task cap `10`
- labeling harvest: support-aware `True`, weak replacement cap `8`, support overlap `0.6`
- labeling support-continuation: enabled `True`, max seed sets `240`, max neighbors `4`, protected `8`
- large-task direct worker: enabled `False`, max tasks `12`, candidate sets `240`, time cap `25.0`
- labeling final judge: `on`, max exact tasks `10`, exact harvest target `16`
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
- root-pool post-final-judge selected/new/replacement/added: `1599` / `1577` / `22` / `1599`
- root-partition post-final feedback selected/added: `0` / `0`
- all redlines zero: `True`
- accepted: `False`

| scale | rows | exact | under300 exact | fail-closed | mean total | max total | mean root | mean partition | mean tree |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10 | 20 | 20 | 20 | 0 | 1.397116 | 4.789049 | 0.900388 | None | 0.316075 |

## Per-Instance

| scale | instance | status | scope | pricing | exact | under300 | total | root | partition | tree | active cols | exact harvest | worker harvest | post-FJ added | post-partition added | terminal | provenance | fail reason |
|---:|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 10 | instance_001 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.684007 | 0.285908 | None | 0.22245 | 80 | 0 | 0 | 70 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_002 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.723338 | 0.319409 | None | 0.228087 | 83 | 0 | 0 | 74 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_003 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.878648 | 0.461739 | None | 0.237086 | 100 | 0 | 0 | 88 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_004 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.78409 | 0.375645 | None | 0.231914 | 75 | 0 | 0 | 64 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_005 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 2.199439 | 1.68914 | None | 0.32888 | 82 | 0 | 0 | 70 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_006 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.945637 | 0.527986 | None | 0.24508 | 86 | 0 | 0 | 76 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_007 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 1.394295 | 0.919517 | None | 0.269725 | 134 | 0 | 0 | 123 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_008 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 1.208465 | 0.772132 | None | 0.258713 | 86 | 0 | 0 | 74 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_009 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 2.15539 | 1.67986 | None | 0.298656 | 86 | 0 | 0 | 75 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_010 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 1.98476 | 1.492961 | None | 0.31117 | 109 | 0 | 0 | 97 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_011 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 4.789049 | 3.985082 | None | 0.619042 | 117 | 0 | 0 | 105 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_012 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 1.033815 | 0.61742 | None | 0.236064 | 98 | 0 | 0 | 86 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_013 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 3.040499 | 1.697691 | None | 1.15882 | 112 | 0 | 0 | 100 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_014 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.908327 | 0.486602 | None | 0.242122 | 77 | 0 | 0 | 65 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_015 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 1.002248 | 0.577279 | None | 0.247581 | 99 | 0 | 0 | 88 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_016 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.766333 | 0.348979 | None | 0.237598 | 76 | 0 | 0 | 66 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_017 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.713433 | 0.327922 | None | 0.202473 | 90 | 0 | 0 | 80 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_018 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 1.144345 | 0.70128 | None | 0.257514 | 83 | 0 | 0 | 77 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_019 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.747568 | 0.326726 | None | 0.242734 | 60 | 0 | 0 | 48 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_020 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.838627 | 0.414483 | None | 0.245791 | 84 | 0 | 0 | 73 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
