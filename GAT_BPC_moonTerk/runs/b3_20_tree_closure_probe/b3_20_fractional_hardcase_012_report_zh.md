# B3 20-scale fractional hardcase 012 闭合报告

实例：`lunar_ice_sp50_020_012_seed829012`

本报告用于验证 full20 中一个 root-fractional 20-task hardcase 是否已经能由 B3 tree 正式闭合。

## 结果

```text
B0 status = DIRECT_DP_BASELINE_OPTIMAL
B0 objective = 5996.219161
B0 wall time = 19.568s

B3 status = BPC_OPTIMAL
B3 scope = BPC_TREE_OPTIMAL
B3 exact_status = BPC_TREE_OPTIMAL
B3 wall time = 123.506s
node_count = 7
open_node_count = 0
incomplete_node_count = 0
global_lb = 5996.219161
global_ub = 5996.219161
global_gap = 0.0
tree issues = []
```

## Node Ledger

| node | parent | depth | sense | status | bound | rounds | integer witness |
| --- | --- | ---: | --- | --- | ---: | ---: | --- |
| node_000 |  | 0 |  | BRANCHED | 5991.76373 | 6 | COLUMN_POOL_EXACT_COVER 5996.219161 match=false |
| node_001 | node_000 | 1 | same_journey | BRANCHED | 5993.888362 | 5 | COLUMN_POOL_EXACT_COVER 5996.219161 match=false |
| node_002 | node_000 | 1 | different_journey | INTEGER_INCUMBENT | 5996.914684 | 9 | RMP_PRIMAL_INTEGER_EXACT_COVER 5996.914684 match=true |
| node_003 | node_001 | 2 | same_journey | BRANCHED | 5995.672005 | 6 | NODE_LP_FRACTIONAL_NO_INTEGER_POOL_SEARCH |
| node_004 | node_001 | 2 | different_journey | INTEGER_INCUMBENT | 5996.219161 | 8 | RMP_PRIMAL_INTEGER_EXACT_COVER 5996.219161 match=true |
| node_005 | node_003 | 3 | same_journey | PRUNED_BY_BOUND | 5998.678579 | 6 | NODE_LP_FRACTIONAL_NO_INTEGER_POOL_SEARCH |
| node_006 | node_003 | 3 | different_journey | INTEGER_INCUMBENT | 5998.027691 | 5 | RMP_PRIMAL_INTEGER_EXACT_COVER 5998.027691 match=true |

## Interpretation

- 012 不再卡在 branch-node feasible seed repair；`different_journey(011,018)` 子节点通过 exact-cover repair 得到可行 seed。
- complete fixed-universe membership RC audit 在每个节点上给出 official node LP certificate。
- 对 fractional RMP primal，B3 不再在完整 priced universe 上跑整数 DP；它直接进入 Ryan-Foster branching 或 bound pruning。
- B0 direct-DP 仍只作为 incumbent / objective 对照，不作为 BPC certificate。
