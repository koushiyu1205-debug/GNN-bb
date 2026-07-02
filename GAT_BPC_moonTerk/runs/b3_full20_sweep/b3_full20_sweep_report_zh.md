# B3 full20 BPC_TREE_OPTIMAL sweep 报告

本报告汇总 `lunar_ice_sp50_020` 的 20 个 20-task 实例。运行方式为串行 B0 direct-DP + B3B branch-and-price tree，不并行，不运行 B2B_R3 慢诊断矩阵。

## 总结

```text
instance_count = 20
BPC_OPTIMAL = 20/20
BPC_TREE_OPTIMAL = 20/20
objective match with B0 within tolerance = 20/20
tree_objective_tolerance = 5e-06
max |B3 incumbent - B0 objective| = 1e-06
open_node_count max = 0
incomplete_node_count max = 0
tree certificate gate issues = none
mean B0 wall time = 13.229097s
mean B3 wall time = 36.054461s
max B3 wall time = 123.490706s
max B3 wall instance = lunar_ice_sp50_020_012_seed829012
max node count = 7
max node count instance = lunar_ice_sp50_020_012_seed829012
branching instances = 2/20
total expanded nodes = 5
```

## 实例结果

| instance | B0 objective | B3 exact | B3 lb | B3 ub | diff vs B0 | nodes | expanded | wall |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 001 | 7386.805908 | BPC_TREE_OPTIMAL | 7386.805908 | 7386.805908 | 0.0 | 1 | 0 | 22.024129 |
| 002 | 6766.890301 | BPC_TREE_OPTIMAL | 6766.890301 | 6766.890301 | 0.0 | 1 | 0 | 21.608686 |
| 003 | 8052.53043 | BPC_TREE_OPTIMAL | 8052.53043 | 8052.53043 | 0.0 | 1 | 0 | 35.18185 |
| 004 | 6290.10408 | BPC_TREE_OPTIMAL | 6290.104079 | 6290.104079 | -1e-06 | 1 | 0 | 28.396842 |
| 005 | 6220.730886 | BPC_TREE_OPTIMAL | 6220.730886 | 6220.730886 | 0.0 | 1 | 0 | 32.778424 |
| 006 | 7865.563256 | BPC_TREE_OPTIMAL | 7865.563256 | 7865.563256 | 0.0 | 1 | 0 | 24.201909 |
| 007 | 7668.079173 | BPC_TREE_OPTIMAL | 7668.079173 | 7668.079173 | 0.0 | 1 | 0 | 17.564385 |
| 008 | 6493.304113 | BPC_TREE_OPTIMAL | 6493.304113 | 6493.304113 | 0.0 | 1 | 0 | 29.871927 |
| 009 | 6989.192613 | BPC_TREE_OPTIMAL | 6989.192613 | 6989.192613 | 0.0 | 1 | 0 | 24.43302 |
| 010 | 6713.181569 | BPC_TREE_OPTIMAL | 6713.181569 | 6713.181569 | 0.0 | 1 | 0 | 30.129801 |
| 011 | 6565.530217 | BPC_TREE_OPTIMAL | 6565.530217 | 6565.530217 | 0.0 | 1 | 0 | 37.101978 |
| 012 | 5996.219161 | BPC_TREE_OPTIMAL | 5996.219161 | 5996.219161 | 0.0 | 7 | 3 | 123.490706 |
| 013 | 6296.161022 | BPC_TREE_OPTIMAL | 6296.161022 | 6296.161022 | 0.0 | 5 | 2 | 79.979307 |
| 014 | 6417.637033 | BPC_TREE_OPTIMAL | 6417.637033 | 6417.637033 | 0.0 | 1 | 0 | 36.389064 |
| 015 | 7423.892019 | BPC_TREE_OPTIMAL | 7423.892019 | 7423.892019 | 0.0 | 1 | 0 | 31.897434 |
| 016 | 6810.417414 | BPC_TREE_OPTIMAL | 6810.417413 | 6810.417413 | -1e-06 | 1 | 0 | 16.182548 |
| 017 | 6086.210264 | BPC_TREE_OPTIMAL | 6086.210263 | 6086.210263 | -1e-06 | 1 | 0 | 41.814597 |
| 018 | 6552.716 | BPC_TREE_OPTIMAL | 6552.716 | 6552.716 | 0.0 | 1 | 0 | 36.995999 |
| 019 | 7107.857934 | BPC_TREE_OPTIMAL | 7107.857934 | 7107.857934 | 0.0 | 1 | 0 | 27.192538 |
| 020 | 7109.354738 | BPC_TREE_OPTIMAL | 7109.354738 | 7109.354738 | 0.0 | 1 | 0 | 23.854067 |

## 证明边界

- B0 direct-DP 只作为 feasible incumbent 和 objective 对照，不作为 BPC certificate。
- B3 的 `BPC_TREE_OPTIMAL` 来自节点级 complete fixed-universe true-dual reduced-cost audit、closed branch tree gate、official node LP bound 和整数 incumbent/pruning 共同闭合。
- 004、016、017 的 `-1e-06` 差值为舍入级，均小于 `TREE_OBJECTIVE_TOLERANCE=5e-06`。
- 本报告覆盖当前 `data/instances/lunar_ice_sp50_020` 文件夹内的 20 个实例；若数据集重新生成，需要重新 sweep。

## 产物

- rows: `runs/b3_full20_sweep/b3_full20_sweep_all_rows.csv`
- summary: `runs/b3_full20_sweep/b3_full20_sweep_summary.json`
