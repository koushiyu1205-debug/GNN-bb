# B3 20-scale BPC_TREE_OPTIMAL 闭合补充验证

本报告只跑 20-scale selected5 的 B0 direct-DP incumbent 与 B3B tree certificate，不跑 B2B_R3 慢诊断矩阵。

- B3B BPC_TREE_OPTIMAL: 5/5
- mean B3 wall time: 27.997986
- max B3 wall time: 35.18185
- max node count: 1
- max incomplete node count: 0
- max |B3 incumbent - B0 objective|: 1e-06
- objective match tolerance: 5e-06
- objective match within tolerance: 5/5

| instance | B0 objective | B3 scope | B3 exact | B3 lb | B3 ub | gap | nodes | wall | issues |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| lunar_ice_sp50_020_001_seed829001 | 7386.805908 | BPC_TREE_OPTIMAL | BPC_TREE_OPTIMAL | 7386.805908 | 7386.805908 | 0.0 | 1 | 22.024129 |  |
| lunar_ice_sp50_020_002_seed829002 | 6766.890301 | BPC_TREE_OPTIMAL | BPC_TREE_OPTIMAL | 6766.890301 | 6766.890301 | 0.0 | 1 | 21.608686 |  |
| lunar_ice_sp50_020_003_seed829003 | 8052.53043 | BPC_TREE_OPTIMAL | BPC_TREE_OPTIMAL | 8052.53043 | 8052.53043 | 0.0 | 1 | 35.18185 |  |
| lunar_ice_sp50_020_004_seed829004 | 6290.10408 | BPC_TREE_OPTIMAL | BPC_TREE_OPTIMAL | 6290.104079 | 6290.104079 | 0.0 | 1 | 28.396842 |  |
| lunar_ice_sp50_020_005_seed829005 | 6220.730886 | BPC_TREE_OPTIMAL | BPC_TREE_OPTIMAL | 6220.730886 | 6220.730886 | 0.0 | 1 | 32.778424 |  |

## 证明边界

- B0 direct-DP 只作为 feasible incumbent / objective 对照，不作为 BPC certificate。
- B3B 的节点证书来自 complete fixed-universe membership reduced-cost audit；final judge source 为 provided complete-universe cache。
- BPC_TREE_OPTIMAL 只有在 node LP certificate、整数 incumbent、closed tree gate 全部通过时声明。
- 004 的 `-1e-06` 目标差来自 B0/B3 输出舍入，低于 `TREE_OBJECTIVE_TOLERANCE=5e-06`，按 tree gate 视为目标一致。

## Full20 hardcase note

selected5 之外，已额外验证 root-fractional hardcase `lunar_ice_sp50_020_012_seed829012`：

- hardcase report: `/home/kai/work/GAT_BPC_moonTerk/runs/b3_20_tree_closure_probe/b3_20_fractional_hardcase_012_report_zh.md`
- status: `BPC_OPTIMAL`
- exact_status: `BPC_TREE_OPTIMAL`
- node_count: `7`
- incomplete_node_count: `0`
- open_node_count: `0`

full20 全量 sweep 已在当前实现下完成：

- full20 report: `/home/kai/work/GAT_BPC_moonTerk/runs/b3_full20_sweep/b3_full20_sweep_report_zh.md`
- BPC_TREE_OPTIMAL: `20/20`
- max incomplete node count: `0`
- max open node count: `0`

当前结论：B3 已实现当前 `lunar_ice_sp50_020` 数据集 20-scale 全量正式闭合。
