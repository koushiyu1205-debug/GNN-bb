# Compact Fixed-Graph Product Oracle Probe Report

## 结论

- 该报告是 fixed-graph product oracle 诊断，不是 BPC root/tree certificate。
- `DIRECT_DP_FIXED_GRAPH_OPTIMAL` 才表示 product oracle 证明最优；有 incumbent 但 time limit 只表示可行上界。

## 汇总

- rows: 1
- product optimal: 0/1
- feasible incumbent: 1/1
- mean row elapsed: 283.804s
- mean objective among incumbents: 1.9146
- mean bound: 1.25962
- mean gap: 0.342096
- max gap: 0.342096
- rows with finite bound: 1/1
- mean/max MIP nodes: 0/0
- mean simplex iterations: 48354
- status counts: {'HIGHS_COMPACT_TIME_LIMIT_REACHED': 1}

## Rows

| instance | status | incumbent | objective | bound | gap | elapsed_s | mip_start |
|---|---|---:|---:|---:|---:|---:|---|
| lunar_ice_sp50_030_001_seed929001 | `HIGHS_COMPACT_TIME_LIMIT_REACHED` | true | 1.9146 | 1.25962 | 0.342096 | 283.804 | OK/instance_reference_solution |
