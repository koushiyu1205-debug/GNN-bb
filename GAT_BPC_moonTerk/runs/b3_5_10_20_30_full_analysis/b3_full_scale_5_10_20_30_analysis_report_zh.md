# B3 5/10/20/30 全量测试详细分析报告

## 1. 测试范围与配置

本轮测试覆盖当前数据目录中的四个主规模：

| scale | instance folder | instance count | max_direct_tasks | 测试语义 |
| ---: | --- | ---: | ---: | --- |
| 5 | `data/instances/lunar_ice_sp50_005` | 20 | 5 | 正式 B3 exact tree closure |
| 10 | `data/instances/lunar_ice_sp50_010` | 20 | 10 | 正式 B3 exact tree closure |
| 20 | `data/instances/lunar_ice_sp50_020` | 20 | 20 | 正式 B3 exact tree closure |
| 30 | `data/instances/lunar_ice_sp50_030` | 20 | 20 | fail-closed diagnostic, 不尝试 exhaustive direct30 |

B3B accepted 配置：

```text
b3_max_columns_per_round = 512
b3_max_rounds_per_node = 16
max_branch_depth = 4
max_tree_nodes = 31
scale30_max_direct_tasks = 20
scale30_policy = fail_closed_guard
tree_objective_tolerance = 5e-06
```

证明边界保持不变：B0 direct-DP 只作为 feasible incumbent 和 objective 对照，不作为 BPC certificate；B3 的 `BPC_TREE_OPTIMAL` 必须来自 node LP certificate、complete fixed-universe reduced-cost audit、closed tree gate、整数 incumbent 或 bound pruning。

## 2. 总体结论

| scale | runs | BPC_TREE_OPTIMAL | NOT_SOLVED | fail-closed | objective match | mean B3 wall | max B3 wall | max nodes | branching instances |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5 | 20 | 20 | 0 | 0 | 20 | 0.305246 | 0.475021 | 1 | 0 |
| 10 | 20 | 20 | 0 | 0 | 20 | 1.27868 | 2.827351 | 1 | 0 |
| 20 | 20 | 20 | 0 | 0 | 20 | 36.054461 | 123.490706 | 7 | 2 |
| 30 | 20 | 0 | 20 | 20 | 0 | 3.8e-05 | 0.000271 | 0 | 0 |

结论可以直接读成三句话：

- 5/10/20 三个规模在当前 fixed-graph exact universe 下全部正式闭合：`BPC_TREE_OPTIMAL = 20/20`。
- 20 规模不只是 root-integral case；`012` 和 `013` 发生了实际 branching，tree 仍然闭合，最大节点数为 7。
- 30 规模没有被声明为最优；当前 exact 上限为 20 task，所以 20/20 个 30-task 实例全部按 `task_count_exceeds_exhaustive_pricing_limit` fail-closed，且 `certificate_leak_count_30 = 0`。

## 3. 按规模分析

### 3.1 5-scale

- 正式闭合：`20/20`。
- B0 objective 对齐：`20/20`，最大绝对差 `0.0`，容差 `5e-06`。
- open node 最大值 `0`，incomplete node 最大值 `0`。
- 平均 B3 wall time `0.305246s`，最大 `0.475021s`，最慢实例 `lunar_ice_sp50_005_012_seed679018`。
- 没有发生实际 branching；全部为 root LP 整数后晋级 `BPC_TREE_OPTIMAL`。

### 3.2 10-scale

- 正式闭合：`20/20`。
- B0 objective 对齐：`20/20`，最大绝对差 `1e-06`，容差 `5e-06`。
- open node 最大值 `0`，incomplete node 最大值 `0`。
- 平均 B3 wall time `1.27868s`，最大 `2.827351s`，最慢实例 `lunar_ice_sp50_010_010_seed729010`。
- 没有发生实际 branching；全部为 root LP 整数后晋级 `BPC_TREE_OPTIMAL`。

### 3.3 20-scale

- 正式闭合：`20/20`。
- B0 objective 对齐：`20/20`，最大绝对差 `1e-06`，容差 `5e-06`。
- open node 最大值 `0`，incomplete node 最大值 `0`。
- 平均 B3 wall time `36.054461s`，最大 `123.490706s`，最慢实例 `lunar_ice_sp50_020_012_seed829012`。
- 有 `2` 个实例发生实际 branching，总 expanded nodes `5`；其余实例 root LP 已整数。

### 3.4 30-scale

- 30-scale 当前不是 exact closure 测试，而是 fail-closed diagnostic。
- `max_direct_tasks=20`，所有 30-task 实例都被 guard 截住：fail-closed `20/20`。
- `BPC_TREE_OPTIMAL = 0/20`，这是预期结果，不是求解失败误报。
- issue 分布：`{'task_count_exceeds_exhaustive_pricing_limit': 20}`。
- 证书泄漏检查：summary 中 `certificate_leak_count_30 = 0`。

## 4. 关键实例

| instance | scale | status | exact | B0 obj | B3 lb | B3 ub | diff | nodes | expanded | wall | note |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| lunar_ice_sp50_005_012_seed679018 | 5 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | 1431.520203 | 1431.520203 | 1431.520203 | 0.0 | 1 | 0 | 0.475021 | scale max wall/root integral |
| lunar_ice_sp50_010_010_seed729010 | 10 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | 3015.878029 | 3015.878029 | 3015.878029 | 0.0 | 1 | 0 | 2.827351 | scale max wall/root integral |
| lunar_ice_sp50_020_012_seed829012 | 20 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | 5996.219161 | 5996.219161 | 5996.219161 | 0.0 | 7 | 3 | 123.490706 | actual branching closure |
| lunar_ice_sp50_020_013_seed829013 | 20 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | 6296.161022 | 6296.161022 | 6296.161022 | 0.0 | 5 | 2 | 79.979307 | actual branching closure |
| lunar_ice_sp50_030_011_seed929011 | 30 | BPC_INCOMPLETE_PRICING | NOT_SOLVED |  |  |  |  | 0 | 0 | 0.000271 | expected fail-closed guard |

## 5. 全量实例明细

### 5-scale rows

| idx | instance_id | exact | diff vs B0 | nodes | expanded | open | incomplete | wall | issues |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | lunar_ice_sp50_005_001_seed679001 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 0.155486 |  |
| 2 | lunar_ice_sp50_005_002_seed679002 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 0.207958 |  |
| 3 | lunar_ice_sp50_005_003_seed679005 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 0.282607 |  |
| 4 | lunar_ice_sp50_005_004_seed679030 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 0.228473 |  |
| 5 | lunar_ice_sp50_005_005_seed679011 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 0.291881 |  |
| 6 | lunar_ice_sp50_005_006_seed679032 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 0.21575 |  |
| 7 | lunar_ice_sp50_005_007_seed679013 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 0.362489 |  |
| 8 | lunar_ice_sp50_005_008_seed679014 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 0.398124 |  |
| 9 | lunar_ice_sp50_005_009_seed679015 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 0.247138 |  |
| 10 | lunar_ice_sp50_005_010_seed679016 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 0.332183 |  |
| 11 | lunar_ice_sp50_005_011_seed679017 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 0.426837 |  |
| 12 | lunar_ice_sp50_005_012_seed679018 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 0.475021 |  |
| 13 | lunar_ice_sp50_005_013_seed679019 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 0.390544 |  |
| 14 | lunar_ice_sp50_005_014_seed679020 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 0.387615 |  |
| 15 | lunar_ice_sp50_005_015_seed679021 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 0.240383 |  |
| 16 | lunar_ice_sp50_005_016_seed679062 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 0.218603 |  |
| 17 | lunar_ice_sp50_005_017_seed679123 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 0.318598 |  |
| 18 | lunar_ice_sp50_005_018_seed679064 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 0.345165 |  |
| 19 | lunar_ice_sp50_005_019_seed679025 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 0.283315 |  |
| 20 | lunar_ice_sp50_005_020_seed679026 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 0.296748 |  |

### 10-scale rows

| idx | instance_id | exact | diff vs B0 | nodes | expanded | open | incomplete | wall | issues |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | lunar_ice_sp50_010_001_seed729001 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 0.800639 |  |
| 2 | lunar_ice_sp50_010_002_seed729002 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 0.475359 |  |
| 3 | lunar_ice_sp50_010_003_seed729023 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 0.781212 |  |
| 4 | lunar_ice_sp50_010_004_seed729004 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 1.034166 |  |
| 5 | lunar_ice_sp50_010_005_seed729045 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 1.857142 |  |
| 6 | lunar_ice_sp50_010_006_seed729086 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 0.796041 |  |
| 7 | lunar_ice_sp50_010_007_seed729007 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 0.922377 |  |
| 8 | lunar_ice_sp50_010_008_seed729068 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 1.27422 |  |
| 9 | lunar_ice_sp50_010_009_seed729069 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 1.154304 |  |
| 10 | lunar_ice_sp50_010_010_seed729010 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 2.827351 |  |
| 11 | lunar_ice_sp50_010_011_seed729011 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 2.231984 |  |
| 12 | lunar_ice_sp50_010_012_seed729072 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 1.443145 |  |
| 13 | lunar_ice_sp50_010_013_seed729053 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 2.171084 |  |
| 14 | lunar_ice_sp50_010_014_seed729034 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 1.089495 |  |
| 15 | lunar_ice_sp50_010_015_seed729015 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 1.962283 |  |
| 16 | lunar_ice_sp50_010_016_seed729016 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 0.898288 |  |
| 17 | lunar_ice_sp50_010_017_seed729037 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 0.774702 |  |
| 18 | lunar_ice_sp50_010_018_seed729118 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 1.286953 |  |
| 19 | lunar_ice_sp50_010_019_seed729039 | BPC_TREE_OPTIMAL | -1e-06 | 1 | 0 | 0 | 0 | 0.810531 |  |
| 20 | lunar_ice_sp50_010_020_seed729040 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 0.982325 |  |

### 20-scale rows

| idx | instance_id | exact | diff vs B0 | nodes | expanded | open | incomplete | wall | issues |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | lunar_ice_sp50_020_001_seed829001 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 22.024129 |  |
| 2 | lunar_ice_sp50_020_002_seed829002 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 21.608686 |  |
| 3 | lunar_ice_sp50_020_003_seed829003 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 35.18185 |  |
| 4 | lunar_ice_sp50_020_004_seed829004 | BPC_TREE_OPTIMAL | -1e-06 | 1 | 0 | 0 | 0 | 28.396842 |  |
| 5 | lunar_ice_sp50_020_005_seed829005 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 32.778424 |  |
| 6 | lunar_ice_sp50_020_006_seed829006 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 24.201909 |  |
| 7 | lunar_ice_sp50_020_007_seed829027 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 17.564385 |  |
| 8 | lunar_ice_sp50_020_008_seed829008 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 29.871927 |  |
| 9 | lunar_ice_sp50_020_009_seed829009 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 24.43302 |  |
| 10 | lunar_ice_sp50_020_010_seed829010 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 30.129801 |  |
| 11 | lunar_ice_sp50_020_011_seed829011 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 37.101978 |  |
| 12 | lunar_ice_sp50_020_012_seed829012 | BPC_TREE_OPTIMAL | 0.0 | 7 | 3 | 0 | 0 | 123.490706 |  |
| 13 | lunar_ice_sp50_020_013_seed829013 | BPC_TREE_OPTIMAL | 0.0 | 5 | 2 | 0 | 0 | 79.979307 |  |
| 14 | lunar_ice_sp50_020_014_seed829014 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 36.389064 |  |
| 15 | lunar_ice_sp50_020_015_seed829015 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 31.897434 |  |
| 16 | lunar_ice_sp50_020_016_seed829016 | BPC_TREE_OPTIMAL | -1e-06 | 1 | 0 | 0 | 0 | 16.182548 |  |
| 17 | lunar_ice_sp50_020_017_seed829017 | BPC_TREE_OPTIMAL | -1e-06 | 1 | 0 | 0 | 0 | 41.814597 |  |
| 18 | lunar_ice_sp50_020_018_seed829018 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 36.995999 |  |
| 19 | lunar_ice_sp50_020_019_seed829019 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 27.192538 |  |
| 20 | lunar_ice_sp50_020_020_seed829020 | BPC_TREE_OPTIMAL | 0.0 | 1 | 0 | 0 | 0 | 23.854067 |  |

### 30-scale rows

| idx | instance_id | exact | diff vs B0 | nodes | expanded | open | incomplete | wall | issues |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | lunar_ice_sp50_030_001_seed929001 | NOT_SOLVED |  | 0 | 0 | 0 | 0 | 2.5e-05 | task_count_exceeds_exhaustive_pricing_limit |
| 2 | lunar_ice_sp50_030_002_seed929002 | NOT_SOLVED |  | 0 | 0 | 0 | 0 | 2.4e-05 | task_count_exceeds_exhaustive_pricing_limit |
| 3 | lunar_ice_sp50_030_003_seed929003 | NOT_SOLVED |  | 0 | 0 | 0 | 0 | 2.1e-05 | task_count_exceeds_exhaustive_pricing_limit |
| 4 | lunar_ice_sp50_030_004_seed929004 | NOT_SOLVED |  | 0 | 0 | 0 | 0 | 2e-05 | task_count_exceeds_exhaustive_pricing_limit |
| 5 | lunar_ice_sp50_030_005_seed929005 | NOT_SOLVED |  | 0 | 0 | 0 | 0 | 2.2e-05 | task_count_exceeds_exhaustive_pricing_limit |
| 6 | lunar_ice_sp50_030_006_seed929006 | NOT_SOLVED |  | 0 | 0 | 0 | 0 | 2.2e-05 | task_count_exceeds_exhaustive_pricing_limit |
| 7 | lunar_ice_sp50_030_007_seed929007 | NOT_SOLVED |  | 0 | 0 | 0 | 0 | 2.1e-05 | task_count_exceeds_exhaustive_pricing_limit |
| 8 | lunar_ice_sp50_030_008_seed929008 | NOT_SOLVED |  | 0 | 0 | 0 | 0 | 2.2e-05 | task_count_exceeds_exhaustive_pricing_limit |
| 9 | lunar_ice_sp50_030_009_seed929009 | NOT_SOLVED |  | 0 | 0 | 0 | 0 | 9.2e-05 | task_count_exceeds_exhaustive_pricing_limit |
| 10 | lunar_ice_sp50_030_010_seed929010 | NOT_SOLVED |  | 0 | 0 | 0 | 0 | 2.2e-05 | task_count_exceeds_exhaustive_pricing_limit |
| 11 | lunar_ice_sp50_030_011_seed929011 | NOT_SOLVED |  | 0 | 0 | 0 | 0 | 0.000271 | task_count_exceeds_exhaustive_pricing_limit |
| 12 | lunar_ice_sp50_030_012_seed929012 | NOT_SOLVED |  | 0 | 0 | 0 | 0 | 2.2e-05 | task_count_exceeds_exhaustive_pricing_limit |
| 13 | lunar_ice_sp50_030_013_seed929013 | NOT_SOLVED |  | 0 | 0 | 0 | 0 | 2.1e-05 | task_count_exceeds_exhaustive_pricing_limit |
| 14 | lunar_ice_sp50_030_014_seed929014 | NOT_SOLVED |  | 0 | 0 | 0 | 0 | 2.1e-05 | task_count_exceeds_exhaustive_pricing_limit |
| 15 | lunar_ice_sp50_030_015_seed929015 | NOT_SOLVED |  | 0 | 0 | 0 | 0 | 2.3e-05 | task_count_exceeds_exhaustive_pricing_limit |
| 16 | lunar_ice_sp50_030_016_seed929016 | NOT_SOLVED |  | 0 | 0 | 0 | 0 | 2.2e-05 | task_count_exceeds_exhaustive_pricing_limit |
| 17 | lunar_ice_sp50_030_017_seed929017 | NOT_SOLVED |  | 0 | 0 | 0 | 0 | 2.2e-05 | task_count_exceeds_exhaustive_pricing_limit |
| 18 | lunar_ice_sp50_030_018_seed929018 | NOT_SOLVED |  | 0 | 0 | 0 | 0 | 2.1e-05 | task_count_exceeds_exhaustive_pricing_limit |
| 19 | lunar_ice_sp50_030_019_seed929019 | NOT_SOLVED |  | 0 | 0 | 0 | 0 | 2.1e-05 | task_count_exceeds_exhaustive_pricing_limit |
| 20 | lunar_ice_sp50_030_020_seed929020 | NOT_SOLVED |  | 0 | 0 | 0 | 0 | 2.1e-05 | task_count_exceeds_exhaustive_pricing_limit |

## 6. 风险与解释

- 5/10/20 的结论是当前 fixed logical graph 和 complete fixed-universe pricing scope 内的正式 BPC tree closure，不是对任意更大物理路径空间的声明。
- 20-scale 的最慢点仍然是 root-fractional branch tree，例如 012 需要 7 个节点、123.49s；但它已经不是 proof-chain blocker。
- 30-scale 当前没有 exact optimality 证据；它只证明 fail-closed guard 正常工作，没有 certificate leakage。要闭合 30，需要新的 pricing universe 表达、completion bound、或更强的 B4/B5 层，而不是把 `max_direct_tasks` 直接拉到 30 硬跑。
- 10-scale 的 019、20-scale 的 004/016/017 出现 `-1e-06` 差值，属于输出舍入级，均低于 `TREE_OBJECTIVE_TOLERANCE=5e-06`。

## 7. 产物

- all rows: `runs/b3_5_10_20_30_full_analysis/b3_full_scale_5_10_20_30_all_rows.csv`
- summary: `runs/b3_5_10_20_30_full_analysis/b3_full_scale_5_10_20_30_summary.json`
- 5/10 raw rows: `runs/b3_5_10_20_30_full_analysis/b3_full_scale_5_10_rows.csv`
- 30 raw rows: `runs/b3_5_10_20_30_full_analysis/b3_full_scale_30_fail_closed_rows.csv`
- 20 source report: `runs/b3_full20_sweep/b3_full20_sweep_report_zh.md`
