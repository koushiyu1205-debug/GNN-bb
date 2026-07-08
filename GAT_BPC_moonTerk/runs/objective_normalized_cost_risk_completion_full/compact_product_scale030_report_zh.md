# Compact Fixed-Graph Product Oracle Probe Report

## 结论

- 该报告是 fixed-graph product oracle 诊断，不是 BPC root/tree certificate。
- `DIRECT_DP_FIXED_GRAPH_OPTIMAL` 才表示 product oracle 证明最优；有 incumbent 但 time limit 只表示可行上界。

## 汇总

- rows: 20
- product optimal: 0/20
- feasible incumbent: 20/20
- mean row elapsed: 63.401s
- mean objective among incumbents: 1.88538
- mean bound: 
- mean gap: 
- max gap: 
- rows with finite bound: 0/20
- mean/max MIP nodes: /
- mean simplex iterations: 
- status counts: {'HIGHS_COMPACT_TIME_LIMIT_REACHED': 20}

## Rows

| instance | status | incumbent | objective | bound | gap | elapsed_s | mip_start |
|---|---|---:|---:|---:|---:|---:|---|
| lunar_ice_sp50_030_001_seed929001 | `HIGHS_COMPACT_TIME_LIMIT_REACHED` | true | 1.9146 |  |  | 64.9499 | OK/instance_reference_solution |
| lunar_ice_sp50_030_002_seed929002 | `HIGHS_COMPACT_TIME_LIMIT_REACHED` | true | 1.83132 |  |  | 65.7463 | OK/instance_reference_solution |
| lunar_ice_sp50_030_003_seed929003 | `HIGHS_COMPACT_TIME_LIMIT_REACHED` | true | 1.82363 |  |  | 65.4325 | OK/instance_reference_solution |
| lunar_ice_sp50_030_004_seed929004 | `HIGHS_COMPACT_TIME_LIMIT_REACHED` | true | 1.9087 |  |  | 65.1408 | OK/instance_reference_solution |
| lunar_ice_sp50_030_005_seed929005 | `HIGHS_COMPACT_TIME_LIMIT_REACHED` | true | 1.97627 |  |  | 65.2955 | OK/instance_reference_solution |
| lunar_ice_sp50_030_006_seed929006 | `HIGHS_COMPACT_TIME_LIMIT_REACHED` | true | 1.9348 |  |  | 62.5998 | OK/instance_reference_solution |
| lunar_ice_sp50_030_007_seed929007 | `HIGHS_COMPACT_TIME_LIMIT_REACHED` | true | 1.58846 |  |  | 62.2498 | OK/instance_reference_solution |
| lunar_ice_sp50_030_008_seed929008 | `HIGHS_COMPACT_TIME_LIMIT_REACHED` | true | 1.8165 |  |  | 62.6432 | OK/instance_reference_solution |
| lunar_ice_sp50_030_009_seed929009 | `HIGHS_COMPACT_TIME_LIMIT_REACHED` | true | 1.89211 |  |  | 62.639 | OK/instance_reference_solution |
| lunar_ice_sp50_030_010_seed929010 | `HIGHS_COMPACT_TIME_LIMIT_REACHED` | true | 1.91447 |  |  | 63.2 | OK/instance_reference_solution |
| lunar_ice_sp50_030_011_seed929011 | `HIGHS_COMPACT_TIME_LIMIT_REACHED` | true | 1.69277 |  |  | 62.8421 | OK/instance_reference_solution |
| lunar_ice_sp50_030_012_seed929012 | `HIGHS_COMPACT_TIME_LIMIT_REACHED` | true | 1.86827 |  |  | 62.2678 | OK/instance_reference_solution |
| lunar_ice_sp50_030_013_seed929013 | `HIGHS_COMPACT_TIME_LIMIT_REACHED` | true | 1.75312 |  |  | 62.3082 | OK/instance_reference_solution |
| lunar_ice_sp50_030_014_seed929014 | `HIGHS_COMPACT_TIME_LIMIT_REACHED` | true | 1.83066 |  |  | 62.5394 | OK/instance_reference_solution |
| lunar_ice_sp50_030_015_seed929015 | `HIGHS_COMPACT_TIME_LIMIT_REACHED` | true | 1.94978 |  |  | 62.5447 | OK/instance_reference_solution |
| lunar_ice_sp50_030_016_seed929016 | `HIGHS_COMPACT_TIME_LIMIT_REACHED` | true | 2.06666 |  |  | 62.3521 | OK/instance_reference_solution |
| lunar_ice_sp50_030_017_seed929017 | `HIGHS_COMPACT_TIME_LIMIT_REACHED` | true | 1.87809 |  |  | 62.9833 | OK/instance_reference_solution |
| lunar_ice_sp50_030_018_seed929018 | `HIGHS_COMPACT_TIME_LIMIT_REACHED` | true | 1.82858 |  |  | 62.4242 | OK/instance_reference_solution |
| lunar_ice_sp50_030_019_seed929019 | `HIGHS_COMPACT_TIME_LIMIT_REACHED` | true | 2.10886 |  |  | 62.1927 | OK/instance_reference_solution |
| lunar_ice_sp50_030_020_seed929020 | `HIGHS_COMPACT_TIME_LIMIT_REACHED` | true | 2.12987 |  |  | 65.669 | OK/instance_reference_solution |
