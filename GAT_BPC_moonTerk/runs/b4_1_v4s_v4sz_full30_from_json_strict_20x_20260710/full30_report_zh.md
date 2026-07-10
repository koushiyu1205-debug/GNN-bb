# B4.1 V4S/V4SZ Full 30-Scale Experiment

## Boundary

- Pool build uses staged true-dual pricing and does not certify by itself unless `BPC_NODE_LP_CERTIFIED` is recorded.
- Final V4S/V4SZ rows are proof-only tree-closure checks from the mature active-column pool.
- `BPC_TREE_OPTIMAL` here means exact optimality for the normalized additive objective, not makespan-in-objective.
- Strict full-solve averages use only `strict_from_json=true`: instance JSON -> staged pool maturity -> final proof/tree gate.
- Reused source-probe rows are proof-tail micro-benchmarks only and are excluded from strict end-to-end averages.

## Summary

- pool rows: `20`
- pool certified: `1`
- strict from-json pool certified: `1` / `20`
- proof rows: `40`
- strict from-json proof rows: `40`

| profile | rows | exact cert | strict rows | strict exact | strict mean end-to-end wall | strict mean final proof wall | mean active cols |
|---|---:|---:|---:|---:|---:|---:|---:|
| V4S | 20 | 0 | 20 | 0 | None | None | None |
| V4SZ | 20 | 0 | 20 | 0 | None | None | None |

## Per-Instance Rows

| instance | strict | phase | profile | status | scope | pricing | active cols | pool wall | proof wall | e2e wall | final judge | note |
|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|---|
| instance_001 | True | pool_build | POOL | BPC_GAP_AVAILABLE | BPC_NODE_LP_CERTIFIED | CERTIFIED_NO_NEGATIVE | 151 | 541.578199 | None | None | None |  |
| instance_001 | True | tree_closure | V4S | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | 151 | 541.578199 | 0.557305 | 542.135504 | None |  |
| instance_001 | True | tree_closure | V4SZ | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | 151 | 541.578199 | 0.551209 | 542.129408 | None |  |
| instance_002 | True | pool_build | POOL | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | 39 | 70.233283 | None | None | None |  |
| instance_002 | True | tree_closure | V4S | POOL_NOT_CERTIFIED |  |  | 39 | 70.233283 | None | None | None | pool was not certified; proof-only tree closure skipped |
| instance_002 | True | tree_closure | V4SZ | POOL_NOT_CERTIFIED |  |  | 39 | 70.233283 | None | None | None | pool was not certified; proof-only tree closure skipped |
| instance_003 | True | pool_build | POOL | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | 39 | 94.934347 | None | None | None |  |
| instance_003 | True | tree_closure | V4S | POOL_NOT_CERTIFIED |  |  | 39 | 94.934347 | None | None | None | pool was not certified; proof-only tree closure skipped |
| instance_003 | True | tree_closure | V4SZ | POOL_NOT_CERTIFIED |  |  | 39 | 94.934347 | None | None | None | pool was not certified; proof-only tree closure skipped |
| instance_004 | True | pool_build | POOL | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | 39 | 60.605907 | None | None | None |  |
| instance_004 | True | tree_closure | V4S | POOL_NOT_CERTIFIED |  |  | 39 | 60.605907 | None | None | None | pool was not certified; proof-only tree closure skipped |
| instance_004 | True | tree_closure | V4SZ | POOL_NOT_CERTIFIED |  |  | 39 | 60.605907 | None | None | None | pool was not certified; proof-only tree closure skipped |
| instance_005 | True | pool_build | POOL | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | 39 | 103.181687 | None | None | None |  |
| instance_005 | True | tree_closure | V4S | POOL_NOT_CERTIFIED |  |  | 39 | 103.181687 | None | None | None | pool was not certified; proof-only tree closure skipped |
| instance_005 | True | tree_closure | V4SZ | POOL_NOT_CERTIFIED |  |  | 39 | 103.181687 | None | None | None | pool was not certified; proof-only tree closure skipped |
| instance_006 | True | pool_build | POOL | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | 39 | 130.580501 | None | None | None |  |
| instance_006 | True | tree_closure | V4S | POOL_NOT_CERTIFIED |  |  | 39 | 130.580501 | None | None | None | pool was not certified; proof-only tree closure skipped |
| instance_006 | True | tree_closure | V4SZ | POOL_NOT_CERTIFIED |  |  | 39 | 130.580501 | None | None | None | pool was not certified; proof-only tree closure skipped |
| instance_007 | True | pool_build | POOL | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | 39 | 41.358427 | None | None | None |  |
| instance_007 | True | tree_closure | V4S | POOL_NOT_CERTIFIED |  |  | 39 | 41.358427 | None | None | None | pool was not certified; proof-only tree closure skipped |
| instance_007 | True | tree_closure | V4SZ | POOL_NOT_CERTIFIED |  |  | 39 | 41.358427 | None | None | None | pool was not certified; proof-only tree closure skipped |
| instance_008 | True | pool_build | POOL | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | 39 | 66.619826 | None | None | None |  |
| instance_008 | True | tree_closure | V4S | POOL_NOT_CERTIFIED |  |  | 39 | 66.619826 | None | None | None | pool was not certified; proof-only tree closure skipped |
| instance_008 | True | tree_closure | V4SZ | POOL_NOT_CERTIFIED |  |  | 39 | 66.619826 | None | None | None | pool was not certified; proof-only tree closure skipped |
| instance_009 | True | pool_build | POOL | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | 39 | 70.815576 | None | None | None |  |
| instance_009 | True | tree_closure | V4S | POOL_NOT_CERTIFIED |  |  | 39 | 70.815576 | None | None | None | pool was not certified; proof-only tree closure skipped |
| instance_009 | True | tree_closure | V4SZ | POOL_NOT_CERTIFIED |  |  | 39 | 70.815576 | None | None | None | pool was not certified; proof-only tree closure skipped |
| instance_010 | True | pool_build | POOL | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | 39 | 60.088018 | None | None | None |  |
| instance_010 | True | tree_closure | V4S | POOL_NOT_CERTIFIED |  |  | 39 | 60.088018 | None | None | None | pool was not certified; proof-only tree closure skipped |
| instance_010 | True | tree_closure | V4SZ | POOL_NOT_CERTIFIED |  |  | 39 | 60.088018 | None | None | None | pool was not certified; proof-only tree closure skipped |
| instance_011 | True | pool_build | POOL | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | 39 | 176.905082 | None | None | None |  |
| instance_011 | True | tree_closure | V4S | POOL_NOT_CERTIFIED |  |  | 39 | 176.905082 | None | None | None | pool was not certified; proof-only tree closure skipped |
| instance_011 | True | tree_closure | V4SZ | POOL_NOT_CERTIFIED |  |  | 39 | 176.905082 | None | None | None | pool was not certified; proof-only tree closure skipped |
| instance_012 | True | pool_build | POOL | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | 39 | 60.082494 | None | None | None |  |
| instance_012 | True | tree_closure | V4S | POOL_NOT_CERTIFIED |  |  | 39 | 60.082494 | None | None | None | pool was not certified; proof-only tree closure skipped |
| instance_012 | True | tree_closure | V4SZ | POOL_NOT_CERTIFIED |  |  | 39 | 60.082494 | None | None | None | pool was not certified; proof-only tree closure skipped |
| instance_013 | True | pool_build | POOL | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | 39 | 102.011133 | None | None | None |  |
| instance_013 | True | tree_closure | V4S | POOL_NOT_CERTIFIED |  |  | 39 | 102.011133 | None | None | None | pool was not certified; proof-only tree closure skipped |
| instance_013 | True | tree_closure | V4SZ | POOL_NOT_CERTIFIED |  |  | 39 | 102.011133 | None | None | None | pool was not certified; proof-only tree closure skipped |
| instance_014 | True | pool_build | POOL | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | 39 | 139.23766 | None | None | None |  |
| instance_014 | True | tree_closure | V4S | POOL_NOT_CERTIFIED |  |  | 39 | 139.23766 | None | None | None | pool was not certified; proof-only tree closure skipped |
| instance_014 | True | tree_closure | V4SZ | POOL_NOT_CERTIFIED |  |  | 39 | 139.23766 | None | None | None | pool was not certified; proof-only tree closure skipped |
| instance_015 | True | pool_build | POOL | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | 39 | 101.266027 | None | None | None |  |
| instance_015 | True | tree_closure | V4S | POOL_NOT_CERTIFIED |  |  | 39 | 101.266027 | None | None | None | pool was not certified; proof-only tree closure skipped |
| instance_015 | True | tree_closure | V4SZ | POOL_NOT_CERTIFIED |  |  | 39 | 101.266027 | None | None | None | pool was not certified; proof-only tree closure skipped |
| instance_016 | True | pool_build | POOL | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | 39 | 114.162526 | None | None | None |  |
| instance_016 | True | tree_closure | V4S | POOL_NOT_CERTIFIED |  |  | 39 | 114.162526 | None | None | None | pool was not certified; proof-only tree closure skipped |
| instance_016 | True | tree_closure | V4SZ | POOL_NOT_CERTIFIED |  |  | 39 | 114.162526 | None | None | None | pool was not certified; proof-only tree closure skipped |
| instance_017 | True | pool_build | POOL | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | 39 | 100.164253 | None | None | None |  |
| instance_017 | True | tree_closure | V4S | POOL_NOT_CERTIFIED |  |  | 39 | 100.164253 | None | None | None | pool was not certified; proof-only tree closure skipped |
| instance_017 | True | tree_closure | V4SZ | POOL_NOT_CERTIFIED |  |  | 39 | 100.164253 | None | None | None | pool was not certified; proof-only tree closure skipped |
| instance_018 | True | pool_build | POOL | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | 39 | 250.279388 | None | None | None |  |
| instance_018 | True | tree_closure | V4S | POOL_NOT_CERTIFIED |  |  | 39 | 250.279388 | None | None | None | pool was not certified; proof-only tree closure skipped |
| instance_018 | True | tree_closure | V4SZ | POOL_NOT_CERTIFIED |  |  | 39 | 250.279388 | None | None | None | pool was not certified; proof-only tree closure skipped |
| instance_019 | True | pool_build | POOL | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | 39 | 221.136885 | None | None | None |  |
| instance_019 | True | tree_closure | V4S | POOL_NOT_CERTIFIED |  |  | 39 | 221.136885 | None | None | None | pool was not certified; proof-only tree closure skipped |
| instance_019 | True | tree_closure | V4SZ | POOL_NOT_CERTIFIED |  |  | 39 | 221.136885 | None | None | None | pool was not certified; proof-only tree closure skipped |
| instance_020 | True | pool_build | POOL | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | 39 | 589.248518 | None | None | None |  |
| instance_020 | True | tree_closure | V4S | POOL_NOT_CERTIFIED |  |  | 39 | 589.248518 | None | None | None | pool was not certified; proof-only tree closure skipped |
| instance_020 | True | tree_closure | V4SZ | POOL_NOT_CERTIFIED |  |  | 39 | 589.248518 | None | None | None | pool was not certified; proof-only tree closure skipped |
