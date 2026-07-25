# Phase 3 Pre-Draft Freeze

> Historical status note (2026-07-23): the pre-draft lock below was released
> by the user's Phase 4 authorization. The frozen mainline, objective, proof
> boundary, evidence classes, and terminology remain active; only the former
> prohibition on manuscript drafting has been superseded.

## Stage Status

- Phase: **3 — pre-draft specification and evidence freeze**
- Status: **COMPLETE**
- Freeze date: 2026-07-23 (Asia/Shanghai)
- Manuscript prose: **LOCKED**
- Active manuscript draft: **none**
- Current task boundary: finish the inputs needed for later drafting without
  writing or extending any paper section.

The English Section 3 text already present in `manuscript_draft.md` predates
this freeze. It is retained only as a non-authoritative consistency-check
artifact. It is not an active manuscript, it does not mark P01–P09 as drafted,
and it cannot be reused without a new user instruction authorizing body-text
drafting.

## Frozen Paper Mainline

The controlling mainline is a **pricing-led, branching-assisted
learning-guided exact Branch-Price-and-Cut framework** for multi-trip lunar
water-ice exploration fleet routing.

| Component | Frozen Role | Evidence Maturity | Proof Authority |
|---|---|---|---|
| Learned pricing guidance | Primarily ranks pricing work, states, expansions, candidate columns, or expensive pricing calls | Design only; future results are `TBD` | None |
| Learned branch guidance | Secondarily ranks candidates that have already passed exact validity construction | Design only; future results are `TBD` | None |
| Deterministic cuts | May strengthen the exact BPC under validity, pricing-compatibility, lineage, and reduced-cost audit rules | Implemented exact-framework component | Exact path only |
| Native exact SPPRC completion | Exhausts the admissible pricing space under true duals and active exact context | Implemented proof-bearing component | Sole source of a no-negative-column proof |
| Exact branching and fallback | Constructs valid children and preserves branch-tree completeness | Implemented proof-bearing component | Exact path only |
| RMP bounds, pruning, termination, optimality | Remain unchanged by learned scores | Implemented proof-bearing component | Exact path only |

No learning action may generate, select, activate, retain, delete, or otherwise
control cuts. No learned score may be represented as a lower bound, a
no-negative-column proof, a branch-validity proof, a branch-completeness proof,
or an optimality proof.

## Frozen P0V2 Objective Contract

The repository contains two objective vocabularies. They must not be merged.

| Layer | Fields or Formula | Current P0V2 BPC Role | Paper Rule |
|---|---|---|---|
| Legacy instance/generator payload | `alpha_discovery_completion`, `beta_journey_end_time`, `gamma_lunar_ice_risk`, `delta_energy`; payload mode may remain `weighted_discovery_completion` | Retained for data compatibility and older scheduling/generation paths | Internal compatibility audit only; never manuscript-facing |
| Executed multi-trip route/BPC objective | normalized operating cost + normalized risk + `0.4 ×` normalized science-weighted completion | Supplies `JourneyColumn.objective`, HiGHS RMP coefficients, Native SPPRC coefficients, objective closure, and frozen-run comparisons | This is the official P0V2 BPC objective |
| Makespan | normalized/reporting fields and post-solve metric | Does not enter multi-trip route pricing or master objective | Report as a metric only |

**Manuscript-wide objective lock.** Every manuscript-facing occurrence,
including abstract, body, equations, figures, tables, results, appendices, and
Chinese translation, must use only normalized operating cost + normalized risk
+ `0.4 ×` normalized science-weighted completion time. The legacy row above is
an internal compatibility audit and must not be transferred into the paper.

For a feasible multi-trip route \(p\), the frozen official cost is

\[
c_p =
\frac{C_p}{C^{\mathrm{ref}}}
+\frac{R_p}{R^{\mathrm{ref}}}
+0.4\frac{T_p^w}{T^{w,\mathrm{ref}}}.
\]

The coefficients are fixed manuscript-wide as \(1\), \(1\), and \(0.4\). The
instance-specific reference quantities
are constructed by `objective_references`. Operating cost contains service
cost, path distance, and energy proxy. The weighted-completion term is the sum
of task science weights times task completion times.

Authoritative implementation anchors:

- `src/lunar_ice_bpc/exact/core/data.py`
- `src/lunar_ice_bpc/exact/core/objective.py`
- `src/lunar_ice_bpc/exact/core/journey.py`
- `src/lunar_ice_bpc/exact/master/journey_rmp.py`
- `src/lunar_ice_bpc/exact/bpc/pricing/backends/native_rcspp.py`
- `native/lunar_spprc/src/pybind_module.cpp`
- `src/lunar_ice_bpc/exact/bpc/solver/branch_tree_solver.py`

The detailed notation and source-to-equation mapping is frozen in
`model_notation_and_equation_register.md`.

## Frozen Exactness Scope

1. Exactness is restricted to the **fixed logical-path solution space**
   induced by the frozen instance, including three declared path alternatives
   per directed logical edge.
2. The optimizer does not generate arbitrary continuous lunar-surface
   trajectories at run time.
3. Mathematical exactness does not prove physical fidelity of terrain,
   illumination, risk, or water-ice proxy layers.
4. Learned ordering may change work order but may not change the feasible
   solution set, accepted reduced-cost rule, exact fallback, or proof state.
5. Any unsupported branch or cut context fails closed rather than being
   omitted from proof-bearing pricing.

## Frozen Evidence Vocabulary

| Class | Meaning | Permitted Verb Pattern |
|---|---|---|
| Strict proof | Derived mathematical or exhaustive exact result with stated assumptions and scope | prove, establish; `certify` only when the exact mechanism and scope are explicit |
| Exactness guarantee | Algorithmic invariant conditional on the frozen interface and complete exact fallback | preserve exactness, guarantee under assumptions |
| Frozen experiment | Machine-readable measured result bound to design, build, instances, and run protocol | report, observe, pass/fail the stated gate |
| Diagnostic signal | Replay, one-pair, shadow-mode, or state-level observation | indicate, diagnose, observe within the tested case |
| Heuristic strategy | Learned or hand-crafted ordering that changes effort but owns no proof | rank, prioritize, order, guide |
| Missing evidence | Required artifact has not been supplied | `TBD`; no result sentence |

Chinese paper-facing text defaults to “证明.” English defaults to
`proof`/`prove`. `Certify`/`certified` is restricted to an explicit derivation,
exhaustive exact search, or formal proof chain with the responsible mechanism
and scope stated. The algorithm is a `framework`, not a `backbone`; the scope
is a solution space or state space, not a `universe`.

## Frozen Drafting Inputs

| Input | Controlling File | Freeze Result |
|---|---|---|
| Mainline and exclusions | `confirmed_motivation.md` | Frozen |
| Claims and maturity | `claim_register.md` | Frozen; learning effects remain `TBD` |
| Project evidence | `evidence_bank.md` | Frozen to the current evidence cutoff |
| Section/paragraph allocation | `section_blueprints.md`; `writing_rationale_matrix.md` | Frozen as an execution plan, not prose |
| Model symbols and equations | `model_notation_and_equation_register.md` | Frozen |
| Section-specific evidence packages | `section_writing_input_packets.md` | Frozen |
| Core literature set | `citation_lock.md` | Twenty-three-source lock with per-source support limits |
| Figures and tables | `figure_asset_map.md`; `result_placeholder_schema.md` | Existing figures classified; missing learning figures remain blocked |
| Result activation | `result_placeholder_schema.md` | M001–M006 and EXP-L0/L1/L2/G/EPOCH gates frozen |
| Terminology | `terminology_policy.md` | Mandatory |

## Phase 3 Completion Gate

| Gate | Result |
|---|---|
| Mainline distinguishes pricing-primary, branching-secondary, and no learned cuts | PASS |
| P0V2 executed objective is separated from legacy alpha/beta/gamma/delta payload fields | PASS |
| Manuscript-wide objective wording is locked to the normalized three-term objective | PASS |
| Model notation and equations are mapped to implementation sources | PASS |
| Exact proofs, guarantees, diagnostics, and heuristics are separated | PASS |
| Every planned section has an evidence/citation/TBD input package | PASS |
| Twenty core citations have a locked role and verification status | PASS |
| Learning result placeholders cannot imply an expected outcome | PASS |
| Existing Section 3 prose is outside the active manuscript state | PASS |
| Manuscript body remains locked | PASS |

Phase 3 completion does not authorize manuscript drafting. A later transition
to body text requires an explicit user instruction naming the section or
drafting scope.
