# Result Placeholder and Activation Schema

## Status

- Schema status: **FROZEN**
- Current learning-result status: **ALL BLOCKED / TBD**
- No-task-wait implementation status: **ACTIVATED FOR THE FROZEN
  SCALE-5--30 EXACT CONTROL**
- Purpose: allow later experiments to be inserted without inventing values or
  changing the paper's mainline after outcomes are known.
- Objective lock: every objective value, equality audit, table, figure, and
  result sentence uses normalized operating cost + normalized risk +
  `0.4 ×` normalized science-weighted completion time.

## Required Missing Materials

| ID | Required Artifact | Minimum Fields | Activation Effect |
|---|---|---|---|
| M001 | Frozen dataset/split/leakage manifest | corpus hash; sample provenance; map/seed/scale groups; train/validation/test IDs; overlap checks; target construction; timestamp | Activates E03 and the data-lineage part of APP04 |
| M002 | Pricing-guidance model package | checkpoint hash; feature schema/version; target/loss; training config; model-selection rule; inference environment; calibration/OOD fields | Activates concrete M13–M16 and E06 details |
| M003 | Branch-ranking model package | checkpoint hash; valid candidate generator; candidate-set hash; labels/targets; evaluation-order log; fallback record | Activates concrete M17–M18 and branch-specific E06 details |
| M004 | Paired L0/L1/L2 ablation | run manifest; exact build/config hashes; schedule; repeats; instances; row-level results; intervals; failures | Activates R06–R09 and FIG15/TAB08 |
| M005 | Safety/overhead/fallback/held-out package | proof-equivalence audit; RC audit; proof-debt counters; false-proof counters; inference time; fallback frequency; held-out/OOD definitions/results | Activates R06, R10, FIG16, D01–D06, and abstract result slot |
| M006 | Paired seasonal operating-phase package | southern-vernal-equinox reference; 12 anchors across one draconic year; four three-anchor phase labels; approximately 28.9-day anchor spacing; scale-dependent 16–76 h mission windows; one-hour environmental samples; window-aggregation rule and variation audit; illumination provenance; fixed task/rover/horizon fields; path-generation config and hashes; common normalization references; exact/infeasible/incomplete rows; paired-family mapping; three-anchor arithmetic phase means for all-exact-feasible family-phases; paired contrasts and uncertainty | Activates R11E, the Section 6.5 result slot, RQ5, and the bounded seasonal-phase discussion |

## Variant Freeze

| Variant | Only Allowed Difference | Invariant Exact Path | Status |
|---|---|---|---|
| L0 | No learned ordering | RMP, exact pricing completion, deterministic cuts, exact branching/fallback, proof ledger | `TBD` experiment |
| L1 | Learned ordering for pricing work | Same as L0 | `TBD` experiment |
| L2 | L1 plus learned ranking over exact-valid branch candidates | Same as L0 | `TBD` experiment |
| G | Held-out/OOD evaluation of L0/L1/L2 | Same exact fallback and proof rules | `TBD` experiment |

There is no learned-cut variant.

All L0/L1/L2/G rows must bind the activated no-task-wait timing policy, the
same objective, and the complete proof context. A legacy wait-permitted row is
not an L0 row for the no-task-wait formulation. Legacy timing and search-work
records are not revised L0 performance rows.

## EXP-L0/L1/L2 Required Row Schema

Each `(instance, repeat, order, variant)` row must contain at least:

| Group | Required Fields |
|---|---|
| Identity | experiment ID; instance ID/hash; map group; scale; repeat; AB/BA order; variant |
| Build/config | git commit; dirty-state flag; native module hash; solver config hash; objective schema/version; cut policy; branch policy |
| Resource environment | hardware/CPU; memory limit; threads; wall-time limit; strict-cold marker |
| Terminal state | exact/incomplete/error status; objective if legal; lower/upper bounds; gap; proof scope |
| Exact-safety | objective-closure delta; reduced-cost reconstruction delta; false exact/no-negative/prune counters; proof-debt outstanding; branch-candidate-set mismatch; cut-context mismatch |
| Pricing workload | calls by mode; labels generated/expanded/dominated; columns found/admitted/duplicate; final-judge calls/time; exact-completion calls/time; fallback count |
| Branch workload | nodes; candidates generated; candidates expensively evaluated; selected candidate rank; child pricing calls/time; fallback reason |
| Learning | model/checkpoint hash; inference calls/time; calibration/OOD score; learned-action acceptance/rejection; fallback trigger |
| Timing/memory | end-to-end time; RMP time; pricing time; branching time; cut time; inference time; peak RSS |
| Provenance | row hash; log path; proof record path; run manifest path |

## Zero-Tolerance Safety Gates

No learning-performance result may be interpreted unless all required gates
pass:

| Gate | Required Value |
|---|---|
| False exact termination | 0 |
| False no-negative-column statement | 0 |
| False node prune | 0 |
| Objective mismatch against L0 exact result | 0 within frozen numerical tolerance |
| Reduced-cost reconstruction mismatch | 0 within frozen numerical tolerance |
| Outstanding proof debt at proof event | 0 |
| Required negative column permanently dropped by learning | 0 |
| Exact-valid branch candidate removed by learning, or fractional no-pair node closed without an exact alternative/aggregation proof | 0 |
| Unsupported branch/cut context accepted by exact pricing | 0 |
| Missing proof or lineage record for an exact claim | 0 |

A safety-gate failure blocks a performance conclusion even if runtime is lower.

## Performance and Mechanism Metrics

| Question | Primary Comparison | Required Metrics | Interpretation Rule |
|---|---|---|---|
| Preservation | L1/L2 vs L0 | all safety gates; objective/proof status | Must pass before other questions |
| Pricing effect | L1 vs L0 | end-to-end time; pricing time; labels; calls; final-judge effort; inference overhead; fallback | Report paired estimate and interval; include regressions |
| Branch increment | L2 vs L1 | end-to-end time; nodes; candidate evaluations; child workload; inference overhead; fallback | Candidate validity set must remain identical |
| Held-out/OOD | G across L0/L1/L2 | closure; workload; inference; calibration/OOD; fallback | State held-out unit and exact fallback behavior |
| Seasonal operating phase | Four phase groups formed from paired window-aggregated epochs with the same tasks, rover data, scale-dependent horizon and normalizers | phase/anchor/window/sampling/aggregation metadata; within-window variation; path changes; exact/infeasible/incomplete status; normalized science-weighted completion time; reporting-only makespan; objective components; resources; route/trip and fleet structure | Use the arithmetic mean of three anchors only for all-exact-feasible family-phases; calculate contrasts on common paired families; exclude incomplete rows from ranking; report infeasibility separately; every exact conclusion remains conditional on its fixed instance |

## Placeholder Tables

### TAB08-A — Safety

| Variant | Exact rows / total | Objective mismatches | RC mismatches | False proofs/prunes | Outstanding proof debt | Candidate-set mismatches |
|---|---:|---:|---:|---:|---:|---:|
| L0 | TBD | TBD | TBD | TBD | TBD | TBD |
| L1 | TBD | TBD | TBD | TBD | TBD | TBD |
| L2 | TBD | TBD | TBD | TBD | TBD | TBD |

### TAB08-B — Pricing Guidance

| Comparison | Paired end-to-end effect | Pricing-time effect | Label effect | Exact-completion/final-judge effect | Inference overhead | Fallback frequency |
|---|---|---|---|---|---|---|
| L1 vs L0 | TBD | TBD | TBD | TBD | TBD | TBD |

### TAB08-C — Incremental Branch Guidance

| Comparison | Paired end-to-end effect | Node effect | Candidate-evaluation effect | Child-workload effect | Inference overhead | Fallback frequency |
|---|---|---|---|---|---|---|
| L2 vs L1 | TBD | TBD | TBD | TBD | TBD | TBD |

### TAB08-D — Held-Out/OOD

| Held-out unit | Variant | Exact closure | Paired effect | OOD/calibration | Fallback | Boundary |
|---|---|---|---|---|---|---|
| TBD | L0/L1/L2 | TBD | TBD | TBD | TBD | TBD |

## Figure Activation

| Figure | Data Requirement | Current Status | Prohibited Before Activation |
|---|---|---|---|
| FIG15 | M004 plus passed M005 safety gates | BLOCKED | directional arrows/colors, speedup labels, estimated bars |
| FIG16 | frozen held-out split in M001 plus M005 results | BLOCKED | generalization/robustness wording or interpolated values |

## Prose Activation Rules

1. R06 activates only after the complete safety table is frozen.
2. R07 activates only after L1-vs-L0 paired rows, intervals, overhead, and
   fallback are frozen.
3. R08 activates only after L2-vs-L1 paired rows and candidate-set equivalence
   are frozen.
4. R09 requires row-level heterogeneity and all failed/incomplete cases.
5. R10 requires a predeclared held-out/OOD unit and frozen results.
6. D01–D03 and the abstract result sentence activate only after the
   corresponding result rows pass.
7. RQ5 and Section 6.5 activate only after M006 binds paired epochs, four
   three-anchor phase labels, common task sets, common normalization
   references, environmental provenance, exact solver rows, family-level
   phase summaries, and uncertainty-aware paired contrasts.
8. A missing or failed artifact remains `TBD`; it is never replaced by an
   expectation, deterministic-SRI result, or diagnostic.
9. Only the frozen scale-5--30 control may currently support a no-task-wait
   computational claim. Legacy wait-permitted results remain only with that
   qualifier, and new revised-model runs are required for every historical
   cut-effect, state-size, or scale-50/100 claim.
