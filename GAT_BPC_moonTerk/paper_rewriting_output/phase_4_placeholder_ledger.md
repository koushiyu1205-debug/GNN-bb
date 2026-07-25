# Phase 4 Placeholder Ledger

## Control Rule

Every empty slot in `manuscript_draft.md` is deliberate. A placeholder may be
replaced only by a frozen artifact whose identity, configuration, rows, and
scope can be traced through the project evidence chain. No placeholder carries
an expected direction, an estimated number, or a provisional favorable
conclusion.

## Missing-Material Placeholders

| ID | Manuscript Locations | Content Deliberately Left Empty | Activation Evidence | Present Status |
|---|---|---|---|---|
| `TBD-M001` | Sections 5.3 and Appendix E | Sample inventory, split, targets, and leakage controls | Frozen dataset and split manifest with hashes, generation policy, target construction, and leakage audit | `TBD` |
| `TBD-M002` | Sections 4.6, 5.5, and Appendix E | Pricing model dimensions, architecture, checkpoint, targets, loss, training schedule, inference path, and schema binding | Immutable pricing-guidance checkpoint and complete training/inference package | `TBD` |
| `TBD-M003` | Sections 4.6, 5.5, and Appendix E | Branch-ranking model, valid-candidate labels, checkpoint, training, and inference package | Immutable branch checkpoint and logs proving that only exact-valid candidates entered the learned ranking set | `TBD` |
| `TBD-M004` | Sections 5.7 and Appendix E | Frozen L0/L1/L2 paired design, repetitions, schedules, row schema, summaries, and uncertainty procedure | Complete paired-run manifests and machine-readable rows for all registered variants | `TBD` |
| `TBD-M005` | Sections 5.8 and Appendix E | Exact-equivalence, inference overhead, fallback, held-out, and out-of-distribution package | Complete safety and generalization artifacts with context hashes and failure records | `TBD` |
| `TBD-M006` | Sections 3.1, 5.2, 6.5, 7.1, 7.3, 7.5, 7.7, and Appendix E | Paired mission-epoch instances and four-phase environmental comparison | Frozen manifest with a southern-vernal-equinox reference, 12 anchors at approximately 28.9-day spacing, four three-anchor phase labels, scale-dependent 16–76 h mission windows, one-hour environmental samples, declared window-aggregation rule, within-window variation audit, paired task sets, path-generation hashes, common normalization references, exact/infeasible/incomplete rows, family-level phase summaries, paired contrasts and uncertainty | `TBD` |

## Missing-Experiment Placeholders

| ID | Manuscript Location | Required Comparison | Required Fields Before Activation | Present Status |
|---|---|---|---|---|
| `TBD-EXP-L0` | Section 6.4 | Frozen no-learning exact control | Per-instance objective/proof status, wall time, pricing calls, labels, columns, nodes, memory, and failure reason | `TBD` |
| `TBD-EXP-L1` | Section 6.4 | Learned pricing guidance versus L0 | Paired end-to-end and pricing-work deltas, inference overhead, proof-debt discharge, fallback, and uncertainty | `TBD` |
| `TBD-EXP-L2` | Section 6.4 | Pricing plus branch ranking versus L1 | Incremental branch-tree effect, valid-candidate coverage, branch inference overhead, fallback, and uncertainty | `TBD` |
| `TBD-EXP-G` | Section 6.4 | Generalization evaluation | Exact closure, calibration/ranking quality, workload, overhead, fallback, and declared failure behavior | `TBD` |
| `TBD-EXP-EPOCH` | Section 6.5 | Paired four-phase seasonal operating comparison | Phase/anchor/window/sampling/aggregation metadata; path-option additions/removals and attribute changes; exact/infeasible/incomplete status; normalized science-weighted completion time; reporting-only makespan; objective components; resources; route/trip and fleet changes; all-exact-feasible three-anchor arithmetic phase means; common-family paired contrasts and uncertainty | `TBD` |

## Result-Dependent Prose Placeholders

| ID | Manuscript Location | Deferred Text | Activation Rule | Present Status |
|---|---|---|---|---|
| `TBD-ABS-RESULT` | Abstract | One bounded empirical result sentence | Activate only after L0/L1/L2 rows and safety gates are frozen; report magnitude, uncertainty, scope, and exact-safety outcome in one sentence | `TBD` |
| `TBD-DISC-RQ1-RQ5` | Section 7.1 | Direct answers to the five registered research questions | Activate each answer only after its corresponding learning or mission-epoch rows exist; an inconclusive answer is acceptable and must remain explicit | `TBD` |
| `TBD-DISC-IMPLICATION` | Section 7.3 | Transportation-system implication of measured solver behavior | Activate only from validated workload and robustness evidence; do not infer field productivity or scientific yield | `TBD` |
| `TBD-DISC-PHASE` | Section 7.3 | Bounded implication of the four-phase comparison | Activate only after M006 and TBD-EXP-EPOCH provide exact paired rows, family-level phase summaries and uncertainty; report metric disagreement and infeasible/incomplete cases | `TBD` |

## Figure Placeholders

The Phase 4 working draft describes the two result figures but does not insert
empty numerical graphics. Their activation is controlled by the experiment
schema:

| ID | Intended Figure | Activation Evidence | Present Status |
|---|---|---|---|
| `TBD-FIG15` | Paired L0/L1/L2 workload and wall-time comparison | Frozen M004 rows and uncertainty calculation | `TBD`; caption location reserved by Section 6.4 |
| `TBD-FIG16` | Inference overhead, fallback, and proof-debt discharge | Frozen M005 rows and exact-safety audit | `TBD`; caption location reserved by Section 6.4 |

## Completeness Check

- All manuscript placeholders are represented in this ledger.
- Repeated M001--M006 entries are intentional cross-references to the same
  missing artifact, not separate missing results.
- Available deterministic evidence remains visible in Section 6 and is not
  relabeled as learned-model evidence.
- Empty learning rows do not interrupt the paper's argument: the method,
  baselines, questions, safety gates, metrics, and interpretation locations are
  already defined.
