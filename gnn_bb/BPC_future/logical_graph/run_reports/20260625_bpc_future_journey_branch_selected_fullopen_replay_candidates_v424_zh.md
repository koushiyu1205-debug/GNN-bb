# V424 full-open selected path strict replay candidates

date = 2026-06-25
entry_count = 6

用途：把 full-open 已经显示真实 OPTIMAL wall-time 下降的 selected branch pair 转成严格 full-replay 候选。

注意：这不是最终标签。只有后续 forced replay 跑完并通过 audit 后，才进入训练数据。

## greedy_tranquillitatis_seed61103 / node 0 depth 0 pair [6, 15]
rule = force_pair_path:0:6,15
source_branch_score = 0.847553492
source limited -> full-open wall = 511.822729 -> 291.713493 (-220.109236s)
run_dir = BPC_future/results/journey_branch_selected_fullopen_replay_candidates_v424_20260625/greedy_tranquillitatis_seed61103_d0_n0_pair_6_15

## greedy_tranquillitatis_seed61103 / node 1 depth 1 pair [7, 9]
rule = force_pair_path:0:6,15=same_vehicle;1:7,9
source_branch_score = 0.592560887
source limited -> full-open wall = 511.822729 -> 291.713493 (-220.109236s)
run_dir = BPC_future/results/journey_branch_selected_fullopen_replay_candidates_v424_20260625/greedy_tranquillitatis_seed61103_d1_n1_pair_7_9

## greedy_tranquillitatis_seed61103 / node 2 depth 1 pair [10, 19]
rule = force_pair_path:0:6,15=separate_vehicle;1:10,19
source_branch_score = 0.44610104
source limited -> full-open wall = 511.822729 -> 291.713493 (-220.109236s)
run_dir = BPC_future/results/journey_branch_selected_fullopen_replay_candidates_v424_20260625/greedy_tranquillitatis_seed61103_d1_n2_pair_10_19

## sector_tranquillitatis_seed61513 / node 0 depth 0 pair [2, 3]
rule = force_pair_path:0:2,3
source_branch_score = 0.656457841
source limited -> full-open wall = 543.580975 -> 466.142748 (-77.438227s)
run_dir = BPC_future/results/journey_branch_selected_fullopen_replay_candidates_v424_20260625/sector_tranquillitatis_seed61513_d0_n0_pair_2_3

## sector_tranquillitatis_seed61513 / node 1 depth 1 pair [2, 19]
rule = force_pair_path:0:2,3=same_vehicle;1:2,19
source_branch_score = 0.622410476
source limited -> full-open wall = 543.580975 -> 466.142748 (-77.438227s)
run_dir = BPC_future/results/journey_branch_selected_fullopen_replay_candidates_v424_20260625/sector_tranquillitatis_seed61513_d1_n1_pair_2_19

## sector_tranquillitatis_seed61513 / node 3 depth 2 pair [14, 20]
rule = force_pair_path:0:2,3=same_vehicle;1:2,19=same_vehicle;2:14,20
source_branch_score = 0.276038319
source limited -> full-open wall = 543.580975 -> 466.142748 (-77.438227s)
run_dir = BPC_future/results/journey_branch_selected_fullopen_replay_candidates_v424_20260625/sector_tranquillitatis_seed61513_d2_n3_pair_14_20

## greedy_apollo_seed61000 / node 0 depth 0 pair [12, 20]
rule = force_pair_path:0:12,20
source_branch_score = 0.351111591
source baseline -> full-open = EXTERNAL_TIME_LIMIT 600.022151 -> OPTIMAL 368.387159
run_dir = BPC_future/results/journey_branch_selected_fullopen_replay_candidates_v424_20260625/greedy_apollo_seed61000_d0_n0_pair_12_20

## greedy_tranquillitatis_seed61001 / node 0 depth 0 pair [3, 4]
rule = force_pair_path:0:3,4
source_branch_score = 0.838095963
source baseline -> full-open = OPTIMAL 327.745824 -> OPTIMAL 58.624806; target_200_candidate = true
run_dir = BPC_future/results/journey_branch_selected_fullopen_replay_candidates_v424_20260625/greedy_tranquillitatis_seed61001_d0_n0_pair_3_4

## greedy_tranquillitatis_seed61846 / auxiliary wall-time improvement
source baseline -> full-open = OPTIMAL 144.820908 -> OPTIMAL 122.461717; already_target_200 = true
rule = force_pair_path:0:5,11; node=0; depth=0; pair=[5, 11]; score=0.799775958
rule = force_pair_path:0:5,11=same_vehicle;1:5,17; node=1; depth=1; pair=[5, 17]; score=0.465402991
rule = force_pair_path:0:5,11=separate_vehicle;1:17,19; node=2; depth=1; pair=[17, 19]; score=0.462968618
