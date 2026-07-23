# Confirmed Motivation

## Confirmation Status

- Status: **CONFIRMED**
- Confirmed by user: 2026-07-23
- Selected research option: **Option B, modified to B+**
- Drafting authorization: **granted for Phase 3 on 2026-07-23**. The current
  user instruction scopes the first drafting pass to Section 3.

## Exact Confirmed Motivation

Exact multi-sortie fleet routing with explicit optimality proofs for lunar
water-ice prospecting is computationally demanding. This paper therefore develops a **pricing-led,
branching-assisted learning-guided exact Branch-Price-and-Cut framework** in
which learned policies primarily prioritize pricing work and secondarily rank
a limited set of branching candidates. Cut generation and cut management are
not learning-guided. Mandatory native exact SPPRC completion, deterministic
valid-cut logic, exact branch-validity and completeness fallbacks, and the
exact BPC path remain solely responsible for official bounds, pruning,
termination, and optimality proofs.

## Contribution Boundary

### Learned components included

1. **Primary — pricing guidance:** learned scores may rank pricing states,
   resource expansions, candidate columns, heuristic-pricing calls, or other
   work-order decisions.
2. **Secondary — branch guidance:** learned scores may rank an already valid
   set of branch candidates or decide which candidates receive expensive
   evaluation first.

### Learned components excluded

Learning must not generate, select, activate, retain, remove, or otherwise
control cuts. SRI or other valid-cut machinery may remain in the exact BPC
algorithm only under deterministic, auditable rules. No learned-cut policy,
learned-cut experiment, or learning-to-cut contribution is part of the paper.

## Exactness and Proof Contract

1. A learned pricing signal is heuristic guidance. Before any
   no-negative-column statement or proof-bearing RMP bound is accepted, the
   required native exact SPPRC completion pass must run.
2. A learned branch score is a candidate ordering signal. Exact rules must
   validate every branch, enforce child construction, and provide a complete
   fallback when the learned ranking is unavailable, rejected, or
   insufficient.
3. Cut validity and cut lifecycle decisions remain deterministic. Learned
   pricing or branching may not bypass the active cut context seen by exact
   pricing.
4. Official lower bounds, node pruning, infeasibility decisions, exact
   termination, and optimality proofs are produced only by the exact
   path.
5. Exactness claims are limited to the frozen fixed logical-path solution space,
   including its three path options per directed logical edge. They do not
   cover every continuous lunar-surface trajectory.

## Required Future Evidence

The future experiment package must distinguish at least:

1. exact BPC without learning guidance;
2. exact BPC with learned pricing guidance only;
3. exact BPC with learned pricing plus learned branch-candidate ranking.

It must report training-data provenance and leakage controls, inference
overhead, exact-fallback frequency, pricing search effort, branching behavior,
end-to-end time and closure outcomes, proof/equivalence audits, and
held-out map or scale behavior. Any unavailable result remains `TBD`. No
runtime reduction, solve-rate improvement, memory benefit, stronger bound, or
generalization claim may be written before frozen evidence supports it.

## Rejected or Modified Options

- **Original Option B:** accepted as the base, then expanded to include a
  secondary learned branch-candidate ranking component.
- **Option A:** rejected because learning across pricing, branching, and cut
  management was broader than requested and would substantially increase the
  experimental burden.
- **Option C:** rejected because it treated learned live-SRI control as the
  main contribution; the confirmed scope excludes learning-guided cuts.

## Forbidden Overclaims

- Do not claim the first learning-guided exact BPC or the first learned
  branching method for exact vehicle-routing BPC.
- Do not describe a learned pricing policy as proof that no negative
  reduced-cost column exists.
- Do not describe a learned branch ranking as a branch-validity or
  branch-completeness proof.
- Do not imply that cut decisions are learned.
- Do not convert diagnostics, replay equivalence, shadow-mode accuracy, or
  heuristic hit rates into solver-performance conclusions.
- Do not generalize optimality within the fixed logical-path solution space to
  continuous lunar terrain.
- Do not fabricate missing experiments, numerical improvements, citations, or
  operational conclusions.
