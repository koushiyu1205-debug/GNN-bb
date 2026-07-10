# B4.1 V4S/V4SZ Full 30-Scale Experiment

## Boundary

- Pool build uses staged true-dual pricing and does not certify by itself unless `BPC_NODE_LP_CERTIFIED` is recorded.
- Final V4S/V4SZ rows are proof-only tree-closure checks from the mature active-column pool.
- `BPC_TREE_OPTIMAL` here means exact optimality for the normalized additive objective, not makespan-in-objective.
- Pool build time and final proof/tree-gate time are reported separately.

## Summary

- pool rows: `1`
- pool certified: `1`
- proof rows: `0`

| profile | rows | exact cert | failed/skipped | mean wall certified | mean final judge certified | mean active cols |
|---|---:|---:|---:|---:|---:|---:|

## Per-Instance Rows

| instance | phase | profile | status | scope | pricing | active cols | wall | final judge | note |
|---|---|---|---|---|---|---:|---:|---:|---|
| instance_001 | pool_build | POOL | BPC_GAP_AVAILABLE | BPC_NODE_LP_CERTIFIED | CERTIFIED_NO_NEGATIVE | 371 | 0.00538 | None | external reuse probe; pool build skipped |
