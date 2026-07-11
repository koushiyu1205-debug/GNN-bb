# B4.1 Exact Final-Judge Harvest Target Ablation

## Boundary

- official objective unchanged: normalized cost + normalized risk + 0.4 * normalized weighted completion.
- This report does not claim any new 30-scale certificate.
- Controlled final-judge rows are diagnostic only; they test true-dual negative harvesting and addability under a deliberately thin feasible RMP.

## Stage A 5-Scale Closure

| target | status | scope | root rounds | added cols | wall sec | redline |
| ---: | --- | --- | ---: | ---: | ---: | --- |
| 1 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | 3 | 19 | 0.188166 | clean |
| 4 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | 3 | 19 | 0.184408 | clean |
| 8 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | 3 | 19 | 0.190481 | clean |

Stage A conclusion: target 1/4/8 all closed the easy 5-scale row in 3 root rounds with 19 added columns. Exact negative harvest was not needed in this case, so this is a safety/regression check, not speed evidence.

## Controlled Final-Judge Negative Harvest

- true B0 objective: `2.191915`.
- thin feasible seed objective: `2.22927` by changing sortie `0` path types to `['low_risk', 'low_risk', 'low_risk', 'low_risk']`.

| target | exact candidates | exact selected | addable selected | new task sets | best RC | worst selected RC |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 35 | 1 | 1 | 1 | -1.569254 | -1.569254 |
| 4 | 35 | 4 | 4 | 4 | -1.569254 | -1.29875 |
| 8 | 35 | 8 | 8 | 8 | -1.569254 | -0.983346 |

Controlled conclusion: the exact labeling final judge returns and addability-audits 1/4/8 true negative columns as requested. This supports using harvest target as a proof-tail batching knob, while keeping no-column certification strictly tied to exact exhaustive proof.

## Redlines

- manual_rc_fail_count: `0`.
- pricing_rc_fail_count: `0`.
- certificate_leak_count: `0`.

## Next Step

Run the same controlled pattern on a 10-scale row only after exact labeling is enabled for that scale, or add a B4.2 cold-start metric that records post-final-judge selected/addable counts separately from worker-selected counts.
