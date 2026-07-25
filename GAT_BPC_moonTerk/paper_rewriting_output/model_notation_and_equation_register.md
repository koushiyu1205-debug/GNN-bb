# Model Notation and Equation Register

## Register Status

- Status: **SYNCHRONIZED WITH THE ENGLISH WORKING DRAFT**
- Date: 2026-07-24
- Purpose: provide one source-backed mathematical contract for the detailed
  formulation and exact-algorithm equations now displayed in
  `manuscript_draft.md`.
- Precedence: current executable objective/master/pricing code outranks legacy
  objective sketches in older design or instance-generation documents.

## Notation Typography Policy

The working draft adopts one convention compatible with the official Elsevier
mathematical-style guidance used for the target journal. Elsevier requires
editable, consistently formatted equations, italic mathematical variables, and
consistent author treatment of non-variable subscripts and superscripts. The
paper therefore applies the following explicit house convention:

- mathematical variables and indices that may vary are italic, including
  \(b,i,j,k,\ell,p,s,n,S,u,v,\omega,\zeta\);
- fixed descriptive labels and acronyms are upright, including
  \(\mathrm{arr}\), \(\mathrm{start}\), \(\mathrm{cmp}\),
  \(\mathrm{srv}\), \(\mathrm{rch}\), \(\mathrm{mis}\),
  \(\mathrm{ref}\), \(\mathrm{rep}\), \(\mathrm{root}\),
  \(\mathrm{SRI}\), \(\mathrm{RF}\), and \(\mathrm{LB}\);
- named functions and operators are upright through standard commands such as
  \(\max\), \(\min\), and `\operatorname{...}`;
- vectors use bold italic notation such as \(\boldsymbol{x}\), whereas set
  families use calligraphic capitals such as \(\mathcal{T}\) and
  \(\mathcal{P}\);
- a descriptive superscript such as the `w` in weighted completion is written
  \(T^{\mathrm{w}}\), not \(T^w\), because it is a fixed label rather than a
  variable exponent.

The logical notation is also fixed manuscript-wide:

- definitions are introduced explicitly in prose and then written with the
  ordinary equality sign \(=\);
- Boolean pruning and blocking rules are written as transparent cases: value
  \(1\) when the stated condition holds and \(0\) otherwise;
- \(A\Rightarrow B\) denotes one-way implication and is used for MILP
  indicators or proved necessary consequences;
- \(A\Leftrightarrow B\) is reserved for a genuine necessary-and-sufficient
  relationship; named rules and candidate sets should normally be stated in
  prose and written with ordinary equality or set-builder notation instead.

Source:
[Elsevier's Writing and Copyediting Style Guide](https://supportcontent.elsevier.com/Support%20Hub/Elsa/28996_Elseviers_Writing_and_Copyediting_Style_Guide.pdf).

## Object Hierarchy

| Level | Symbol | Definition | Source Anchor | Scope Note |
|---|---|---|---|---|
| Mission-epoch set | \(\mathcal Q\) | Selected environmental epochs used to generate independent planning instances | C063; CL039; future M006 | External scenario set, not an optimization state |
| Instance | \(\mathcal I\), or \(\mathcal I^{\zeta}\) when the epoch must be shown | Frozen graph, path options, tasks, fleet/resources, time windows, and objective settings for epoch \(\zeta\in\mathcal Q\) | `data/manifests/`; `core/data.py`; future M006 | Defines the fixed exactness scope of one solve; M006 evidence is still TBD |
| Epoch anchor | \(b_\zeta\) | Start time locating mission window \(\zeta\) within the draconic year | C063; future M006 | Planned design starts from the southern vernal equinox, uses approximately 28.9 Earth days between 12 anchors, and groups three anchors into each of four seasonal phases |
| Mission window | \(\mathcal W_\zeta=[b_\zeta,b_\zeta+H^{\mathrm{mis}}]\) | Finite execution window summarized into one independently frozen instance | benchmark horizon manifest; future M006 | Distinct from the spacing between epoch anchors |
| Logical graph | \(\mathcal G=(\mathcal V,\mathcal E)\) | Depot and task sites connected by directed logical edges | `core/data.py`; benchmark instances | Not a continuous terrain graph |
| Tasks | \(\mathcal T\) | Prospecting/service requirements | `core/data.py` | Each task is covered exactly once |
| Rover set | \(\mathcal K\) | Available identical fleet units under the current master interpretation | `core/data.py`; `journey_rmp.py` | One selected multi-trip route consumes one rover |
| Path options | \(\mathcal A_{uv}\) | Declared alternatives for directed edge \((u,v)\) | instance `path_options`; `domain/scenario.py` | Current benchmark uses three alternatives |
| Path-option arcs | \(\mathcal L\) | All triples \((u,v,\omega)\) available to trip-level decisions | `gurobi_compact.py`; instance `path_options` | Distinct from the alternatives on one edge |
| Trip slots | \(\mathcal S=\{1,\ldots,\bar S\}\), \(\bar S=|\mathcal T|\) | Ordered potential trips inside one multi-trip route | `gurobi_compact.py`; `journey_pricing.py` | Active slots are consecutive; the bound is nonrestrictive because every active trip contains a distinct task |
| Trip | \(s\) | Depot-to-depot ordered task sequence with path choices and resources | `core/columns.py` (`TimedSortie`) | Not a master column by itself |
| Multi-trip route | \(p=(s_1,\ldots,s_{m_p})\) | One rover's compatible ordered sequence of one or more trips | `core/journey.py` (`JourneyColumn`) | Master column |
| Feasible route set | \(\mathcal R(\mathcal I)\) | All feasible one-rover multi-trip routes induced by the frozen instance | design contract; exact pricing | Distinct from fleet schedules |
| Fleet-schedule solution space | \(\Omega(\mathcal I)\) | Exact-cover selections of at most \(|\mathcal K|\) routes from \(\mathcal R(\mathcal I)\) | route master; Theorem 1 | Fixed logical-path solution space used by global optimality claims |
| Node route set | \(\mathcal P(n)\) | Multi-trip routes in \(\mathcal R(\mathcal I)\) compatible with node \(n\) | exact pricing; branch context | Full node master uses this set |
| Master variable | \(\lambda_p\) | Selects multi-trip route \(p\) | `journey_rmp.py`; `branch_tree_solver.py` | Binary in the integer master, continuous in RMP |
| Trip arc variable | \(x_{\ell s}\) | Selects path option \(\ell\) in trip \(s\) | `gurobi_compact.py`; implicit in exact columns and Native SPPRC | Exposes the compact flow-equivalent formulation |
| Trip visit variable | \(y_{is}\) | Indicates that trip \(s\) visits task \(i\) | `gurobi_compact.py`; implicit in the ordered task sequence | Trip-level, not a master variable |
| Trip activation variable | \(z_s\) | Indicates that trip \(s\) is active | `gurobi_compact.py`; implicit in a generated route | Trip-level, not a master variable |
| Service times | \(t_{is}^{\mathrm{start}},t_{is}^{\mathrm{cmp}}\) | Start and completion time of task \(i\) in trip slot \(s\) | `gurobi_compact.py`; `core/columns.py` | Descriptive superscripts are upright |
| Trip times | \(t_s^0,t_s^{\mathrm{return}},t_s^{\mathrm{rch}},t_s^{\mathrm{end}}\) | Departure, depot return, recharge and end time | `gurobi_compact.py`; `core/columns.py` | Descriptive superscripts are upright |

## Input and Resource Notation

| Symbol | Meaning | Source Field |
|---|---|---|
| \(r_i,D_i\) | task ready time and due time | task time-window fields |
| \(\sigma_i\) | service duration | task service time |
| \(q_i\) | collected load/demand | task demand/ice quantity |
| \(w_i\) | science weight | task science-weight field |
| \(g_i\) | service energy | task service-energy field |
| \(c_i^{\mathrm{srv}}\) | service cost | task service-cost field |
| \(\tau_{uv}^{\omega}\) | travel time of option \(\omega\) | `travel_time_min` |
| \(e_{uv}^{\omega}\) | travel energy proxy | `energy_proxy` |
| \(\rho_{uv}^{\omega}\) | integrated path risk | `risk_integral` |
| \(d_{uv}^{\omega}\) | path distance | `path_distance_km` |
| \(h_{uv}^{\omega}\) | shadow exposure | `shadow_exposure_min` |
| \(Q\) | rover load capacity | `Q_ice` / `capacity` |
| \(B\) | usable energy limit | `B_use` / `energy_limit` |
| \(H^{\max}\) | maximum shadow exposure per trip | `max_shadow_exposure_per_sortie` |
| \(H^{\mathrm{mis}}\) | mission horizon | `horizon_min` |
| \(\Delta^{\mathrm{env}}\) | temporal resolution of environmental samples used before optimization | future M006; C063 uses one-hour samples |
| \(d^{\mathrm{dock}}\) | docking overhead | `dock_overhead_min` |
| \(P^{\mathrm{rch}}\) | recharge-power proxy | `recharge_power_proxy_per_min` |
| \(\theta_i,\eta_i\) | local task thermal-risk and shadow scores | `local_thermal_risk`, `local_shadow_score` |

## Manuscript Equation Map

The `EQ-*` identifiers below remain stable internal register identifiers. They
are distinct from the sequential displayed equation numbers in the working
manuscript. The current manuscript map is:

| Manuscript tag | Mathematical role | Primary source anchor | Exact/proof scope |
|---:|---|---|---|
| (1) | grid-path distance and sampled surface mean | `domain/real_maps.py::_path_metrics` | frozen instance generation |
| (2) | trip sequence and selected path options | `exact/core/columns.py` | fixed logical-path model |
| (3) | arrival, waiting, service start and completion | `exact/core/columns.py` | exact transition |
| (4a) | depot/task flow, trip activation, task count, route-level uniqueness and consecutive slot activation | `exact/solver/gurobi_compact.py` | core trip-level MILP definition |
| (4b) | trip-level binary variable domains | `exact/solver/gurobi_compact.py` | core trip-level MILP definition |
| (5) | subtour elimination / trip elementarity | `native/lunar_spprc/src/native_pricer.cpp` visited-task state; optional compact connectivity constraints | embedded in feasible columns and exact pricing |
| (6a) | task time windows, selected-arc temporal propagation and inter-trip sequencing | `exact/solver/gurobi_compact.py`; `exact/core/columns.py` | indicator form of core temporal feasibility |
| (6b) | trip load, energy, shadow, risk, operating cost and weighted completion | `exact/core/columns.py`; `exact/core/objective.py` | exact column construction |
| (7) | recharge, due-time and trip resource feasibility | `exact/core/columns.py` | exact feasibility |
| (8) | multi-trip route aggregation | `exact/core/journey.py` | exact column construction |
| (9) | positive componentwise single-task reference quantities | `exact/core/objective.py::objective_references` | normalization contract |
| (10) | normalized operating cost + risk + \(0.4\) weighted completion | `exact/core/objective.py` | sole official objective |
| (11) | reporting-only makespan | `exact/core/objective.py`; `exact/core/journey.py` | not in master/pricing |
| (12) | integer multi-trip route master | `exact/master/journey_rmp.py` | exact model |
| (13) | true route reduced cost | `exact/master/journey_rmp.py`; native pricing | pricing/audit identity |
| (14) | proof-gated node-bound pruning | `exact/certificates/node_bound.py`; `exact/bpc/solver/branch_tree_solver.py` | official bounds only |
| (15) | addability-aware negative-column harvest | `exact/bpc/pricing/harvest.py` | guidance may order only |
| (16) | resource and time-window pruning | exact column/native label feasibility | exact feasibility |
| (17) | guarded native label dominance | `native/lunar_spprc/src/native_pricer.cpp` | context-compatible only |
| (18) | positive-dual completion-bound pruning | `native/lunar_spprc/src/native_pricer.cpp`; `completion_bounds.py` | empty proved branch/cut context |
| (19) | exhaustive no-negative reduced-cost condition | exact pricing/final-judge contracts | proof-bearing only after full completion |
| (20) | root-node divisor-two SRI-3 inequality and coefficient | `exact/core/cuts.py`; `exact/bpc/cuts/live_sri.py::LiveSriPolicy.named("P0")` | deterministic valid root cut |
| (21) | root SRI-3 activity, violation, candidate set, deterministic order and retained harvest | `exact/bpc/cuts/live_sri.py` | complete enumeration of configured triples at the root only |
| (22) | Ryan--Foster co-occurrence, fractionality and candidate-set definition | `exact/solver/branch_probe.py`; exact branching | candidate construction; no-pair is not integrality |
| (23) | unresolved deferred-pricing indicator and necessary condition for a proof-bearing conclusion | `exact/bpc/certificates/proof_debt_queue.py` | every delayed item is registered immediately with unreconstructed reduced cost and must be resolved before proof |
| (24) | node integer optimum over the active route, branch and cut context | integer master (12); `branch_tree_solver.py` | fixed logical-path solution space |
| (25) | equality of the closed RMP and full node-LP optima | exact true-dual pricing; strong LP duality | exact arithmetic and exhaustive compatible pricing |
| (26) | disjoint and exhaustive Ryan–Foster child partition | `exact/core/branching.py`; `branch_tree_solver.py` | exact-valid pair; otherwise fail closed |
| (27) | tree-level incumbent equals the root integer optimum | `branch_tree_solver.py` tree gates and certificate ledger | conditional overall exactness theorem |

## Frozen Equation Register

### EQ-01 — Timing transition

\[
t_{js}^{\mathrm{arr}}
=t_{j-1,s}^{\mathrm{cmp}}+\tau_{i_{j-1},i_j}^{\omega_{j-1}},
\quad
t_{js}^{\mathrm{start}}=\max\{t_{js}^{\mathrm{arr}},r_{i_j}\},
\quad
t_{js}^{\mathrm{cmp}}=t_{js}^{\mathrm{start}}+\sigma_{i_j}.
\]

- Source: `src/lunar_ice_bpc/exact/core/columns.py` and Native SPPRC
  transitions.
- Draft use: Section 3 and Appendix A.
- Constraint: use the same timing convention in dominance and terminal
  feasibility.

### EQ-01A — Core trip topology, activation, and elementarity

\[
\sum_{\ell\in\delta^+(0)}x_{\ell s}
=z_s
=\sum_{\ell\in\delta^-(0)}x_{\ell s},
\qquad
\sum_{\ell\in\delta^-(i)}x_{\ell s}
=y_{is}
=\sum_{\ell\in\delta^+(i)}x_{\ell s},
\qquad
z_s\le\sum_{i\in\mathcal T}y_{is}\le Mz_s.
\]

\[
\sum_{s\in\mathcal S}y_{is}\le 1,
\qquad
1\le\sum_{s\in\mathcal S}z_s,
\qquad
z_{s+1}\le z_s,
\qquad
x_{\ell s},y_{is},z_s\in\{0,1\},
\qquad
t_{is}^{\mathrm{start}},t_{is}^{\mathrm{cmp}},
t_s^0,t_s^{\mathrm{return}},t_s^{\mathrm{rch}},t_s^{\mathrm{end}}\ge0,
\]

\[
\qquad
\sum_{\substack{\ell=(u,v,\omega):\\u,v\in U}}x_{\ell s}\le |U|-1,
\quad
\varnothing\ne U\subseteq\mathcal T.
\]

- Source: explicit arc-balance, activation, task-count, task-uniqueness, slot
  order, and variable-domain rows plus optional connectivity formulations in
  `src/lunar_ice_bpc/exact/solver/gurobi_compact.py`; ordered elementary
  columns in `exact/core/columns.py`; visited-task rejection in
  `native/lunar_spprc/src/native_pricer.cpp`.
- Draft use: Eqs. (4a)–(5) and their feasible-column explanation.
- Constraint: these are core trip-level conditions embedded in the feasible
  multi-trip route set, not additional rows of the route master. Optional cover,
  pair-incompatibility, slot-bound, and big-\(M\) tightenings are not base
  constraint families.

### EQ-01B — Time windows, arc propagation, and trip sequencing

\[
r_i y_{is}\le t_{is}^{\mathrm{start}}
\le (D_i-\sigma_i)y_{is},
\qquad
t_{is}^{\mathrm{cmp}}=t_{is}^{\mathrm{start}}+\sigma_i y_{is},
\]

\[
x_{(i,j,\omega),s}=1
\Rightarrow
t_{js}^{\mathrm{start}}\ge
t_{is}^{\mathrm{cmp}}+\tau_{ij}^{\omega},
\qquad
z_{s+1}=1
\Rightarrow
t_{s+1}^0\ge t_s^{\mathrm{end}}.
\]

- Source: `src/lunar_ice_bpc/exact/solver/gurobi_compact.py`;
  `src/lunar_ice_bpc/exact/core/columns.py`.
- Draft use: Eq. (6a) and the Section 4.3 constraint-to-label mapping.
- Constraint: the manuscript uses MILP indicator notation; implementation
  big-\(M\) values must be valid bounds derived from horizons, windows, and
  travel times rather than fitted coefficients.

### EQ-02 — Recharge and trip end

\[
t_s^{\mathrm{rch}}=d^{\mathrm{dock}}z_s+\frac{E_s}{P^{\mathrm{rch}}},
\qquad
t_s^{\mathrm{end}}=t_s^{\mathrm{return}}+t_s^{\mathrm{rch}}.
\]

- Source: `core/columns.py`; instance vehicle fields.
- Draft use: trip/multi-trip route compatibility.
- Constraint: a next trip cannot start before the previous trip ends.

### EQ-03 — Trip feasibility

\[
Q_s\le Qz_s,\qquad
E_s\le Bz_s,\qquad
H_s\le H^{\max}z_s,\qquad
t_s^{\mathrm{end}}\le H^{\mathrm{mis}}z_s,
\]

with every served task completed by its due time.

- Source: `core/columns.py`; exact pricing resources.
- Draft use: Section 3 definition and Section 4 label resources.
- Constraint: risk is an objective quantity unless a source-backed feasibility
  threshold is explicitly present.

### EQ-04 — Multi-trip route operating cost and weighted completion

\[
C_p=C_p^{\mathrm{service}}+D_p+E_p,
\qquad
T_p^{\mathrm{w}}=\sum_{i\in\mathcal T_p}w_i\,t_{ip}^{\mathrm{cmp}}.
\]

- Source: `core/objective.py::operating_cost_value`;
  `JourneyColumn.discovery_completion_term`.
- Draft use: objective definition.
- Constraint: do not substitute the legacy raw alpha/beta/gamma/delta sum.
- Manuscript lock: use EQ-05 everywhere the objective appears, including
  abstract, body, tables, figures, results, appendices, and translation.

### EQ-05 — Official P0V2 BPC column objective

\[
c_p =
\frac{C_p}{C^{\mathrm{ref}}}
+\frac{R_p}{R^{\mathrm{ref}}}
+0.4\frac{T_p^{\mathrm{w}}}{T^{\mathrm{w},\mathrm{ref}}}.
\]

The coefficients are fixed manuscript-wide as \(1\), \(1\), and \(0.4\).

- Source:
  `core/objective.py::objective_breakdown`,
  `core/journey.py::build_journey_column`,
  `master/journey_rmp.py`,
  `bpc/pricing/backends/native_rcspp.py`,
  `native/lunar_spprc/src/pybind_module.cpp`,
  and `bpc/solver/branch_tree_solver.py`.
- Draft use: official problem objective, master cost, pricing, and objective
  audit.
- Constraint: retain `0.4` in every manuscript-facing occurrence; do not
  substitute a variable or an alternative coefficient.

### EQ-06 — Reference quantities

\[
C^{\mathrm{ref}}=\sum_{i\in\mathcal T}C_i^{\mathrm{single}},\quad
R^{\mathrm{ref}}=\sum_{i\in\mathcal T}R_i^{\mathrm{single}},\quad
T^{\mathrm{w},\mathrm{ref}}
=\sum_{i\in\mathcal T}T_i^{\mathrm{w},\mathrm{single}},
\]

subject to the implemented positive fallback for an infeasible single-task
reference.

- Source: `core/objective.py::objective_references`.
- Draft use: Appendix A or a notation-table note.
- Constraint: describe the fallback exactly if expanded; do not imply an
  externally calibrated physical normalization.

### EQ-07 — Reporting-only makespan

\[
M^{\mathrm{rep}}
=\max_{p:\lambda_p=1}\max_{i\in\mathcal T_p}t_{ip}^{\mathrm{cmp}}.
\]

- Source: `core/journey.py`; `core/objective.py` payload note.
- Draft use: metric definition in Sections 3 and 5.
- Constraint: makespan does not enter EQ-05, RMP coefficients, or Native SPPRC
  objective coefficients.

### EQ-08 — Integer multi-trip route master

\[
\begin{aligned}
\min_{\lambda}\quad&
\sum_{p\in\mathcal P}c_p\lambda_p\\
\mathrm{s.t.}\quad&
\sum_{p\in\mathcal P}a_{ip}\lambda_p=1 && i\in\mathcal T,\\
&
\sum_{p\in\mathcal P}\lambda_p\le |\mathcal K|,\\
&
\sum_{p\in\mathcal P}a_{hp}\lambda_p\le b_h && h\in\mathcal H(n),\\
&
\lambda_p\in\{0,1\} && p\in\mathcal P(n).
\end{aligned}
\]

- Source: `master/journey_rmp.py`; `branch_tree_solver.py`; deterministic cut
  context.
- Draft use: Section 3.
- Constraint: task coverage remains equality; one multi-trip route is one
  rover's ordered trip schedule. \(\mathcal H(n)\) contains only active, valid,
  pricing-compatible deterministic cuts.

### EQ-09 — Restricted master

Replace \(\mathcal P(n)\) in EQ-08 by the current finite
\(\mathcal P'(n)\subseteq\mathcal P(n)\) and relax
\(\lambda_p\in[0,1]\).

- Source: `master/journey_rmp.py`.
- Draft use: Section 3/4 bridge.
- Constraint: an RMP optimum is not a node bound suitable for proof until
  exact pricing closure and all required audits hold.

### EQ-10 — Multi-trip route reduced cost

\[
\bar c_p
=
c_p-\sum_{i\in\mathcal T}\pi_i a_{ip}
-\mu
-\sum_{h\in\mathcal H(n)}\gamma_h a_{hp}.
\]

- Source: `master/journey_rmp.py::manual_journey_reduced_cost`; native pricing
  payload and cut dual context.
- Draft use: pricing definition and proof audit.
- Constraint: signs must follow the implementation's returned dual convention.
  Branch decisions restrict \(\mathcal P(n)\); they are not extra dual terms.

### EQ-11 — Proof-bearing pricing condition

\[
\min_{p\in\mathcal P(n)}\bar c_p\ge -\varepsilon_{\mathrm{rc}}
\]

may support a no-negative-column statement only when the true-dual Native exact
SPPRC completion is exhaustive for the active branch/cut context and its
proof/audit record passes.

- Source: exact-pricing and final-judge contracts; EV004.
- Draft use: Section 4 exactness proof.
- Constraint: heuristic or learned pricing results cannot establish EQ-11.

### EQ-12 — Branch context

\[
\mathcal P(n)
=
\{p\in\mathcal P:
p\text{ satisfies all same/different-route decisions on the path to }n\}.
\]

- Source: Ryan–Foster branching modules and branch contracts.
- Draft use: Section 4 branching.
- Constraint: learned branch scores rank an exact-valid candidate set only.
  If no exact-valid pair or proved alternative disjunction is available, the
  node must remain incomplete rather than being declared integral.

### EQ-13 — Complete-algorithm exactness

\[
z_{\mathrm{RMP}}(n)=z_{\mathrm{LP}}(n)\le z^*(n),
\qquad
\mathcal F(n)
=\mathcal F(n_{ij}^{\mathrm{same}})
\cup\mathcal F(n_{ij}^{\mathrm{different}}),
\qquad
\mathcal F(n_{ij}^{\mathrm{same}})
\cap\mathcal F(n_{ij}^{\mathrm{different}})
=\varnothing .
\]

When every tree gate is satisfied,

\[
z^{\mathrm{inc}}=z^*(n_0).
\]

- Source: manuscript Lemmas 1–5 and Theorem 1; exact RMP, pricing, SRI,
  branch-context, node-bound, deferred-pricing and tree-proof contracts.
- Draft use: Section 4.7 and Appendix A.
- Constraint: this is a conditional exact-arithmetic proof within the fixed
  logical-path solution space. Finite-precision runs are tolerance-qualified,
  and any open or incomplete node blocks the tree-level conclusion.

## Objective Schema Compatibility Register

This register is internal audit material only. Its legacy-field rows must not
be copied into manuscript-facing text. The manuscript may present only EQ-05
and the reporting-only status of EQ-07.

| Field | Loaded by `core/data.py` | Used by EQ-05 in current BPC | Permitted Paper Interpretation |
|---|---:|---:|---|
| `alpha_discovery_completion` | yes | no | Legacy payload/generator provenance |
| `beta_journey_end_time` | yes | no | Legacy payload/generator provenance; completion bounds explicitly exclude it |
| `gamma_lunar_ice_risk` | yes | no | Legacy payload/generator provenance |
| `delta_energy` | yes | no | Legacy payload/generator provenance |
| `weight_operating_cost` | yes | yes | Official normalized operating-cost coefficient |
| `weight_risk` | yes | yes | Official normalized-risk coefficient |
| `weight_completion` | yes | yes | Official normalized weighted-completion coefficient |
| `weight_makespan_metric_only` | yes | no | Reporting configuration only |
| payload `mode=weighted_discovery_completion` | may remain | no | Compatibility label, not executed P0V2 BPC objective semantics |
| `OBJECTIVE_MODE=normalized_operating_cost_risk_weighted_completion` | code constant | yes | Official executed objective schema |

## Proof and Guidance Interface Register

| Operation | Learned Layer May Act? | Exact Check/Fallback | May Affect Official Proof State? |
|---|---:|---|---:|
| Rank pricing work | yes | true-dual exact completion | no |
| Delay a pricing item for finite time | conditionally | every resulting deferred-pricing obligation must be resolved before proof | no |
| Permanently discard a required negative column | no | exact admission/completion | no |
| Rank Ryan–Foster candidates | yes | exact candidate validity; exact alternative branch or incomplete outcome | no |
| Create branch children | no | exact branch constructor | yes, exact path only |
| Generate/manage cuts | no | deterministic valid-cut rules | yes, exact path only |
| Accept bound or prune node | no | exact RMP/pricing/proof chain | yes, exact path only |
| Declare optimality | no | exact branch-tree closure within fixed logical-path solution space | yes, exact path only |

## Precedence and Change Control

1. A later code change to `JourneyColumn.objective`, RMP coefficients, Native
   objective coefficients, or reference construction invalidates EQ-05 and
   requires this register to be refreshed.
2. A new global makespan objective requires a master-level variable,
   constraints, matching pricing semantics, and new frozen evidence; it cannot
   be added editorially.
3. A new learned action requires an explicit safe interface, fallback,
   experiment slot, and claim-register update before it appears in prose.
4. A new path generator changes the exactness scope and requires new instance
   and proof-boundary language.
