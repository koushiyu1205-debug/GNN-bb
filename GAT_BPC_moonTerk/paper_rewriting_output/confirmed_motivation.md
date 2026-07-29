# Confirmed Motivation

## Confirmation Status

- Status: **CONFIRMED**
- Confirmed by user: 2026-07-23
- Selected research option: **Option B, modified to B+**
- Drafting authorization: **active for Phase 4**. The latest user instruction
  authorizes a complete English working draft while requiring unimplemented
  learning, training, and experiment content to remain explicit `TBD`
  placeholders.
- Existing Section 3 text: the former consistency-check artifact may inform
  the new draft only after reconciliation with the frozen equation register.
- Write boundary: all Phase 4 edits are restricted to
  `paper_rewriting_output/`.

## Exact Confirmed Motivation

Exact multi-trip fleet routing with explicit optimality proofs for lunar
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
control cuts. The paper retains only deterministic root-node SRI-3 under the
frozen P0 policy. Descendants may inherit admitted root cuts but perform no new
SRI separation. No learned-cut policy, alternative subset size, learned-cut
experiment, or learning-to-cut contribution is part of the paper.

## Exactness and Proof Contract

1. A learned pricing signal is heuristic guidance. Before any
   no-negative-column statement or proof-bearing RMP bound is accepted, the
   required native exact SPPRC completion pass must run.
2. A learned branch score is a candidate ordering signal. Exact rules must
   validate every branch, enforce child construction, and provide a complete
   fallback when the learned ranking is unavailable, rejected, or
   insufficient.
3. Root-node SRI-3 validity and lifecycle decisions remain deterministic.
   Learned pricing or branching may not bypass the inherited active-cut
   context seen by exact pricing, and nonroot nodes generate no new SRI.
4. Official lower bounds, node pruning, infeasibility decisions, exact
   termination, and optimality proofs are produced only by the exact
   path.
5. Exactness claims are limited to the frozen fixed logical-path solution space,
   including its three path options per directed logical edge. They do not
   cover every continuous lunar-surface trajectory.

## Objective Contract

All manuscript-facing material must use one objective only: normalized
operating cost plus normalized risk plus `0.4 ×` normalized science-weighted
completion time. This contract applies to the title/abstract if the objective
is mentioned, all body sections, equations, figures, tables, results,
appendices, and the Chinese translation package. Legacy
alpha/beta/gamma/delta payload fields are internal compatibility information
and must not appear in manuscript-facing text.

## Lunar-Scene Narrative Contract

The user confirmed on 2026-07-24 that the lunar setting must be technically
specific without territorial or slogan-like framing. The application is
therefore opened through the gap between remote/sample evidence of lunar water
and the in-situ evidence still required at candidate sites, then developed
through candidate-site geography, terrain-aware path alternatives, cumulative
shadow exposure, prospecting service modes, repeated depot returns, recharge,
and science-weighted completion. Chang'E-5 sample evidence may support
heterogeneous host materials and formation or retention factors, but it must
not be used to infer abundance or accessibility at the benchmark's south-pole
sites. The common
`50 km × 50 km` map extent and configured higher-mobility regime are
forward-looking benchmark assumptions rather than claims about current rover
capability. Permanently shadowed regions are important candidate cold-trap
environments, but the manuscript must not claim that all lunar water ice is
confined to them. The text must not use ownership, appropriation, resource-race
or land-rush language, and it must not create a named "time-sensitive resource
exploration" problem class.

The revised Introduction supplied by the user on 2026-07-24 also fixes the
service-window interpretation. Direct sunlight is not a hard prerequisite for
detection, sampling or drilling in the benchmark scenario. Predefined task
time windows provide a static representation of externally specified
instrument, communication-schedule and mission-planning restrictions;
communication dynamics are not introduced as a separate optimization
resource. A further user decision on 2026-07-25 prohibits waiting at candidate
task sites and en route. Waiting is allowed only at the support depot, and the
departure time of each depot-to-depot trip may be adjusted so that every
selected task is reached within its service window. A fixed task/path sequence
is feasible only when one common trip departure satisfies every shifted task
window; prescribed task service is execution rather than waiting. Depot
waiting contributes to elapsed mission time and the mission horizon, but it
does not consume trip-level load, travel energy, path risk, or off-depot shadow
exposure under the forward-looking assumption that the support base supplies
standby power and thermal control. Cumulative
shadow exposure remains distinct from energy consumption and path risk. The
unresolved data placeholder in the supplied paragraph is
resolved only through verified project provenance: the common regional
benchmark uses locally available LOLA-derived elevation, slope, roughness, PSR
and average solar-visibility rasters, while the 30 km/h maximum modeled speed
remains a forward-looking scenario parameter.

The frozen revised solver implements arrival-equals-service-start timing,
common depot-departure adjustment, and no task-site or en-route waiting. Its
new 80-row scale-5--30 package supports revised-model closure and descriptive
timing claims. Earlier cut, state, and scale-50/100 experiments retain the
predecessor wait-permitted qualifier. The proof-bearing implementation retains
unequal-travel-time path options, limits path replacement to the recorded
travel-time equality tolerance, disables active-trip dominance, and permits
depot subset dominance only with the nonempty-set, cut-state, and
branch-continuation guards in Eq. (17).

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
- Do not frame the application through ownership priority, territorial
  competition, resource-race or land-rush language.
- Do not present the `50 km × 50 km` scenario or configured rover mobility as
  a current hardware capability or validated mission performance.
- Do not claim that all lunar water ice occurs only in permanently shadowed
  regions or that project proxies establish in-situ abundance.
- Do not define a separate "time-sensitive resource exploration" problem
  category.
- Do not fabricate missing experiments, numerical improvements, citations, or
  operational conclusions.
