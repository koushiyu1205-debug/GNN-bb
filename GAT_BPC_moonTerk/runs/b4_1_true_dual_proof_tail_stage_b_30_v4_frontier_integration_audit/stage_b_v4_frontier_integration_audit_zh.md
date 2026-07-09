# B4.1 Stage B V4 Frontier Integration Audit

## Boundary

- This is a diagnostic frontier integration audit, not a BPC certificate.
- V4 compact pricing can find columns and improve the frontier bound, but certificate remains suppressed unless true no-negative proof closes.

## Key Evidence

- 60s V4 best frontier LB: `-0.198360699`.
- 600/900s V4 best frontier LB: `-0.007881834`.
- V4 replay best RC: `-0.0080034`, dual bound: `-0.008003885`.
- Merge active columns: `297` -> `298`, added=`True`.

## Staged Resume

| stage | resume cols | active cols | added | rounds | state | scope | best neg RC | final phase | final best RC | final dual bound | elapsed s |
|---:|---:|---:|---:|---:|---|---|---:|---|---:|---:|---:|
| 1 | 298 | 300 | 2 | 3 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | -0.005703396 | optimization_proof | 0.035646975 | -0.192496096 | 595.500219 |
| 2 | 300 | 301 | 1 | 2 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | -0.006394256 | optimization_proof | 0.0102109 | -0.179285852 | 592.348639 |
| 3 | 301 | 302 | 1 | 2 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | -0.006368 | optimization_proof | 0.007385063 | -0.165591678 | 587.023451 |
| 4 | 302 | 304 | 2 | 3 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | -0.004995927 | negative_feasibility_search | None | None | 601.887824 |

## Conclusion

- V4 long proof materially improves the frontier LB and finds an addable negative column.
- After merge and staged resume, the active pool grows from 298 to `304` and adds `6` columns.
- Stages 1-3 show positive final best RC but negative final dual bound, which means proof-bound/coverage remains the blocking condition.
- Stage 4 consumes the budget before an optimization-proof bound is available, so the report must not infer no-negative from that row.
- The correct status remains `DIAGNOSTIC_PRICING_FRONTIER`.
