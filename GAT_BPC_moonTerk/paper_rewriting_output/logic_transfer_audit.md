# Logic Transfer Audit

## Scope

This audit checks whether the Phase 4 working draft transfers the project's
actual model, algorithm, evidence, and limitations rather than replacing them
with a generic learning-guided optimization story.

## Transfer Map

| Source Logic | Manuscript Destination | Transfer Check | Result |
|---|---|---|---|
| Remote/sample evidence versus in-situ prospecting need | Section 1 and draft reference map | C061--C062 support heterogeneous lunar-water host materials and formation/retention factors, while the text explicitly withholds any inference about abundance or accessibility at south-pole benchmark sites | `PASS` |
| Common real-map regional scenario | Abstract, Sections 1, 3.1 and 5.2 | The 50 km by 50 km extent, common base map, task-density scaling and configured higher-mobility regime are transferred as forward-looking benchmark assumptions rather than current rover performance | `PASS` |
| Static prospecting-service window interpretation | Section 1 and model assumptions | EV034 and CL040 transfer direct-sunlight independence and static task windows as bounded representations of externally specified operating restrictions; communication dynamics do not become a separate resource or departure-time-dependent path state | `PASS` |
| No-task-wait timing policy | Abstract, Sections 1, 3.1--3.2, 4.3, 4.7, 5--8 and Appendix A | EV035--EV037 and CL041--CL042 require arrival equals service start, no waiting at candidate tasks or en route, depot-only waiting, adjustable trip departures, feasible-departure logic, and a strict boundary between the revised baseline and historical wait-permitted runs | `PASS WITH FROZEN IMPLEMENTATION BINDING` |
| Mission-epoch environmental representation | Sections 1, 3.1, 5.1--5.2, 6.5, 7.3--7.7 and Appendix A | C063 supports hourly full-cycle and equinox/solstice-linked polar-shadow analysis; C064 supports season-conditioned illumination for landing, power and traverse design; the manifest supplies 16–76 h horizons; four equal phase groups remain the present experiment's stratification; path attributes stay fixed within each solve; M006 and EXP-EPOCH remain empty | `PASS` |
| Lunar candidate-site and path-resource structure | Abstract, Sections 1, 2.1, 3.1--3.2 and 4.1--4.3 | PSR interiors/rims and surrounding access terrain motivate detect/sample/drill tasks, time/energy/risk path alternatives and cumulative shadow exposure without exclusive-water or proxy-as-ground-truth claims | `PASS` |
| Fixed directed logical graph with three declared path options per directed edge | Sections 3.1, 5.2, 7.4, and 7.5 | Exactness is scoped to the fixed logical-path solution space and excludes continuous terrain | `PASS` |
| Lunar path-metric preprocessing | Section 3.1, Eq. (1) and adjacent scope paragraph | Path distance is displayed; slope, roughness, shadow, PSR, crater-edge, steep-slope and directional-elevation summaries are traced to immutable stored attributes without elevating uncalibrated mixing coefficients to scientific model equations | `PASS` |
| Trip-level MILP semantics | Section 3.2, Eqs. (4a)--(7) | Flow, activation, task count and uniqueness, binary domains, elementarity, time propagation, resources, recharge and trip sequencing are explicit, then traced to feasible columns and native label enforcement | `PASS` |
| Multi-trip route columns | Sections 3.2 and 3.3 | Trip, route, compatibility, incidence, and route-master roles remain distinct | `PASS` |
| Trip service/resource reconstruction | Section 3.2, Eqs. (3)--(8) | The revised timing model replaces task-site and en-route waiting by depot departure intervals while preserving service energy, local shadow, the precomputed service-risk contribution, operating cost, weighted completion, recharge and all other defining limits; prescribed service is distinguished from idle waiting, and the internal risk conversion is not exposed as an optimization coefficient | `PASS WITH IMPLEMENTATION BOUNDARY` |
| Executed P0V2 objective | Abstract, Sections 1, 3.3, and 8 | Only normalized operating cost + normalized risk + 0.4 times normalized science-weighted completion time appears as the objective | `PASS` |
| Implemented objective references | Section 3.3, equation (9) | Componentwise feasible singleton references, positive floor and tracked fallback survive without being described as external physical calibration | `PASS` |
| Makespan implementation/reporting boundary | Section 3.3 | Makespan is explicitly reporting-only | `PASS` |
| HiGHS RMP and persistent column lifecycle | Sections 3.3 and 4.2, equations (12)--(15) | Master variables, constraints, duals, objective closure, column identity and addability-aware true-negative harvest survive | `PASS` |
| Native exact SPPRC | Sections 4.3 and 4.7, equations (16)--(19), (23), and (25) | The proof-bearing implementation shifts a common depot departure, stores its latest feasible value, disables active-trip dominance, guards depot subset dominance, disables completion-bound pruning under active cuts, retains true-dual completion, and fails closed | `PASS AS IMPLEMENTED AND TESTED` |
| Deterministic live SRI | Sections 4.4, 6.2, 6.3, Appendices B--C, and Eqs. (20)--(21) | Root-only SRI-3 under P0 retains its divisor-two coefficient, integer-validity derivation, complete triple enumeration, deterministic retention and evidence boundaries | `PASS` |
| Ryan--Foster branching and fail-closed no-pair handling | Sections 4.5, 4.6.3, and 4.7, equations (22) and (26) | Co-occurrence, fractionality, deterministic order, exact child partition and no-pair incompleteness precede learned ranking | `PASS` |
| Typed guidance shadow/safety shell | Sections 4.6--4.7 | Context binding, uncertainty, fail-closed behavior, no-model state, and absent checkpoint are retained | `PASS` |
| Overall exactness proof chain | Section 4.7, Lemmas 1--5, Theorem 1 and Eqs. (24)--(27) | Canonical-route completeness, route-master equivalence, node-LP dual closure, valid cuts, exact child partitions, guidance invariance, tree induction and numerical scope are transferred without claiming unconditional completion | `PASS` |
| Pricing-led, branching-assisted mainline | Title, Abstract, Sections 1, 4, 5, 7, and 8 | Pricing is primary, branch ranking secondary, and no learned cut variant exists | `PASS` |
| Frozen no-task-wait baseline | Section 6.1 | The new root-only-SRI-3 control reports 80/80 exact and correctness outcomes with scale-wise descriptive timing | `PASS` |
| Formal P0 SRI promotion study | Section 6.2 | Correctness success and the scale-30 performance failure jointly show that the candidate does not satisfy the complete promotion criterion | `PASS` |
| State projection/packing audit | Section 6.3 | State sizes, replay equivalence, and one diagnostic pair retain their distinct evidence classes | `PASS` |
| Scale-50/100 bounded runs | Section 6.6 and Appendix D | Memory-limit, legal incomplete, zero proof leak, and absence of exact conclusion survive | `PASS` |
| Missing learning artifacts | Sections 4--7 and Appendix E | M001--M005 and L0/L1/L2/G are visible and do not acquire invented values | `PASS` |
| Missing mission-epoch artifacts | Sections 5--7 and Appendix E | M006 and EXP-EPOCH are visible and do not acquire invented instance or result values | `PASS` |
| Target-journal literature positioning | Sections 1--2 and draft reference map | Twenty-four locked sources support context and positioning only | `PASS` |

## Logic-Loss Checks

- No legacy objective payload field was transferred into the manuscript.
- No uncalibrated lunar mixing coefficient was presented as a scientific model
  parameter.
- No benchmark extent or configured rover-speed parameter was presented as a
  current hardware capability or validated mission result.
- No measured instrument or communication schedule was claimed, and no
  dynamic communication constraint was added to the optimization model.
- No statement confines all lunar water ice to permanently shadowed regions,
  and no territorial, resource-race, land-rush or named time-sensitive problem
  framing entered the manuscript.
- No route-local topology, temporal, resource, or elementarity condition was
  mistaken for a missing route-master row; the Section 4.3 mapping identifies
  its exact pricing implementation.
- Only the frozen revised scale-5--30 control is attributed to the
  no-task-wait formulation; every historical wait-permitted result retains
  its model qualifier.
- No nonroot SRI separation or alternative subset size entered the paper
  scope.
- No implementation scaffold was promoted to a trained-model result.
- No deterministic SRI evidence was relabeled as learning evidence.
- No diagnostic or benchmark-only timing was generalized.
- No independent mission-epoch instance was described as an intra-route
  departure-time-dependent transition, and no rolling update was described as
  a completed or globally exact adaptive policy.
- Epoch-anchor spacing, one-hour environmental sampling and the scale-dependent
  routing horizon remain distinct quantities.
- Kloos et al. is not used to justify task completion or prescribe a
  29.5-day routing horizon.
- No fail-closed incomplete record was converted into an optimal or
  infeasibility conclusion.
- No learned action acquired authority over cuts, bounds, pruning, proof, or
  exact completion.

## Verdict

**PASS WITH AN EXPLICIT EVIDENCE BOUNDARY.** The no-task-wait decision has
been transferred to timing, path-option preprocessing, label dominance, proof
assumptions, terminology, implementation evidence, and the frozen scale-5--30
baseline. Historical cut, state-refinement, and scale-50/100 measurements
remain outside the revised-model evidence class.

## 2026-08-03 Chinese narrative-transfer check

- The six-paragraph Introduction preserves the author-confirmed logic and exactly three contribution groups.
- The model still uses arrival equals service start, no task/en-route waiting, depot-only departure delay and a fixed mission epoch per solve.
- Equations (1)–(15b) and (16)–(28) retain their prior mathematical roles; new Equation (15c) makes the vehicle dual, return cost, SRI-3 coefficient and terminal reduced cost explicit rather than changing the feasible set.
- The objective remains normalized operating cost + risk + 0.4 times science-weighted completion time; makespan remains reporting-only.
- Root-only SRI-3 and deterministic Ryan–Foster branching remain the only cut and branch mechanisms in scope.
- GAT remains a within-base-return-class, within-reduced-cost-bin ordering signal; it does not filter labels or control feasibility, dominance, costs, bounds, cuts, branching, pruning or termination.
- The exact baseline remains 80/80 proved optimal for 5–30 tasks and 15/20 for 50 tasks; the five incomplete pricing runs remain non-conclusive.
- The LOLA average-illumination product is separated from the LOLA permanently-shadowed-region layer used for route shadow exposure.
- Multi-epoch results remain absent, and the independent fixed-instance design is not restated as a departure-time-dependent path model.

**Verdict: PASS for logic transfer; learning, component-ablation and mission-epoch result claims remain inactive.**
