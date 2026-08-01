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

- model: `P0V4_BIDIRECTIONAL_MIDPOINT_ALL_SCALE_CANDIDATE_V2_S50_native_rcspp_bidirectional_midpoint_hybrid_v1`
- config hash: `f57bfd126fef10fa`
- root engine: `b2b_r3_worker`
- worker pricer: `relaxed_labeling`, max task cap `50`
- labeling harvest: support-aware `True`, weak replacement cap `8`, support overlap `0.6`
- labeling support-continuation: enabled `True`, max seed sets `240`, max neighbors `4`, protected `8`
- large-task direct worker: enabled `False`, max tasks `12`, candidate sets `240`, time cap `25.0`
- labeling final judge: `on`, max exact tasks `50`, exact harvest target `128`
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
- root-pool post-final-judge selected/new/replacement/added: `141373` / `141356` / `17` / `141360`
- root-partition post-final feedback selected/added: `0` / `0`
- all redlines zero: `True`
- accepted: `False`

| scale | rows | exact | under300 exact | fail-closed | mean total | max total | mean root | mean partition | mean tree |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 50 | 20 | 11 | 2 | 9 | 1887.740083 | 3617.76369 | 1439.674155 | None | 151.781328 |

## Per-Instance

| scale | instance | status | scope | pricing | exact | under300 | total | root | partition | tree | active cols | exact harvest | worker harvest | post-FJ added | post-partition added | terminal | provenance | fail reason |
|---:|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 50 | instance_001 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | False | 378.257389 | 338.071462 | None | 37.385202 | 7390 | 0 | 0 | 7335 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 50 | instance_002 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | False | 466.294019 | 320.048384 | None | 143.147497 | 7641 | 0 | 0 | 7586 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 50 | instance_003 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 286.789693 | 232.986572 | None | 50.925526 | 6944 | 0 | 0 | 6889 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 50 | instance_004 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 216.170089 | 191.728512 | None | 22.010142 | 5336 | 0 | 0 | 5281 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 50 | instance_005 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | False | 879.477785 | 546.840063 | None | 330.634545 | 3611 | 0 | 0 | 3556 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 50 | instance_006 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER |  | False | False | 3617.720556 | 0.0 | None | None | None | 0 | 0 | 0 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | STAGE_SUBPROCESS_TIMEOUT: command exceeded 3614.624s fail-closed |
| 50 | instance_007 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | False | 445.653568 | 398.968567 | None | 43.248197 | 8173 | 0 | 0 | 8118 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 50 | instance_008 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 3595.522108 | 3592.531209 | None | None | 7238 | 0 | 0 | 7183 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 50 | instance_009 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 3594.642884 | 3590.994325 | None | None | 12515 | 0 | 0 | 12463 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 50 | instance_010 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 3595.490227 | 3592.533816 | None | None | 8810 | 0 | 0 | 8755 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 50 | instance_011 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 3597.93646 | 3594.309706 | None | None | 12219 | 0 | 0 | 12165 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 50 | instance_012 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 3595.043565 | 3591.892034 | None | None | 7991 | 0 | 0 | 7936 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 50 | instance_013 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 3596.023961 | 3592.550291 | None | None | 12397 | 0 | 0 | 12342 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 50 | instance_014 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 3594.608764 | 3591.746269 | None | None | 7085 | 0 | 0 | 7030 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 50 | instance_015 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | False | 302.979248 | 259.291092 | None | 40.75078 | 5872 | 0 | 0 | 5817 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 50 | instance_016 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | False | 444.258593 | 415.580065 | None | 24.92461 | 8295 | 0 | 0 | 8240 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 50 | instance_017 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | False | 660.509808 | 268.617531 | None | 388.697658 | 6385 | 0 | 0 | 6330 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 50 | instance_018 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | False | 551.459907 | 491.679464 | None | 55.971665 | 9137 | 0 | 0 | 9082 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 50 | instance_019 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER |  | False | False | 3617.76369 | 0.0 | None | None | None | 0 | 0 | 0 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | STAGE_SUBPROCESS_TIMEOUT: command exceeded 3614.167s fail-closed |
| 50 | instance_020 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | False | 718.199354 | 183.113733 | None | 531.898791 | 5307 | 0 | 0 | 5252 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
