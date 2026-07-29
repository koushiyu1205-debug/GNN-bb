# Active Section 3 Consistency Audit

## Artifact Scope

- Status: **ACTIVE / SYNCHRONIZED WITH `manuscript_draft.md`**
- Intended manuscript unit: Section 3, *Problem Setting and Mathematical Formulation*
- Active file: `manuscript_draft.md`
- Draft language: English
- Audit date: 2026-07-24
- Blueprint rows executed in active manuscript: P01–P09 plus PROB-2A and the
  route-connectivity unit PROB-5A
- Learning-performance claims: none

## Compact Outline

1. Define the directed logical transportation network and task attributes.
2. Define the three declared path options, display path distance, and trace
   lunar terrain/illumination preprocessing to immutable stored attributes
   without displaying uncalibrated mixing coefficients.
3. Separate mathematical exactness from map and physical fidelity.
4. Define timed depot-to-depot trips with detailed load, energy, shadow,
   service-risk, cost, weighted-completion, recharge, and horizon relations.
5. Display the core route-local MILP families—flow, activation, task count and
   uniqueness, binary domains, elementarity, time propagation, resource
   limits, recharge and trip sequencing—then identify their
   feasible-column/native-SPPRC implementation.
6. Define multi-trip rover routes and exact task-incidence coefficients.
7. Define the positive componentwise single-task normalizers.
8. State the normalized additive objective and the reporting-only makespan.
9. Formulate the integer multi-trip route master and its restricted LP.
10. Derive the shared reduced-cost expression and keep branch restrictions as
   feasibility context rather than dual terms.

## Reverse Outline

| Unit | Paragraph Role | Topic-Sentence Test | Dependency Check | Status |
|---|---|---|---|---|
| S3-OPEN | Scope and terminology | Opens by naming the transportation decisions represented by the model | Introduces path option, trip, and multi-trip route before symbols | PASS |
| P01 | Network and task inputs | Opens with task, rover, depot, and graph notation | Supplies entities used in all later equations | PASS |
| P02 | Path-option space and lunar preprocessing boundary | Opens with the finite option set, displays distance in (1), then identifies the layers summarized into stored attributes | Supplies immutable movement attributes without presenting unsupported calibration | PASS |
| P03 | Exactness scope | Opens with an explicit discrete-scope statement | Bounds all later optimality language | PASS |
| P04-A | Trip sequence and timing | Opens by defining a depot-to-depot trip | Timing recurrence follows declared path choices | PASS |
| P04-A2 | Core trip-level MILP | Displays flow, activation, task count and uniqueness, binary domains, subtour elimination, time propagation, resource limits, recharge and trip sequencing in (4a)–(7), then explains their column/pricer implementation | Makes the full defining MILP logic visible without duplicating trip-level rows in the master | PASS |
| P04-B | Trip resources, objective components and feasibility | Reconstructs load, energy, shadow, risk, cost and completion from arc/visit variables before return/recharge constraints | Uses only implemented resources and coefficients | PASS |
| P05 | Multi-trip route column | Opens by defining a one-rover multi-trip schedule | Separates route, trip, and path option | PASS |
| P06 | Normalizers and official objective | Defines positive componentwise singleton references before the three-term objective | Matches the current normalization and objective implementation | PASS |
| P07 | Makespan boundary | Opens by excluding makespan from the objective | Prevents incompatible objective transfer | PASS |
| P08 | Integer multi-trip route master | Opens with the feasible column set and decision variable | Task cover, fleet, and deterministic-cut rows match the model contract | PASS |
| P09 | Restricted master and reduced cost | Opens with the LP relaxation and pricing relation | One expression serves pricing, admission, and audit | PASS |

## Claim–Evidence Map

| Claim | Evidence | Status |
|---|---|---|
| Tasks, rover capacity, time windows, service resources, and directed path-option attributes are instance inputs | `src/lunar_ice_bpc/exact/core/data.py`; EV010–EV011 | supported |
| The current benchmark declares three path alternatives per directed logical edge | `CODEX_lunar_gat_bpc_exact_algorithm_design.md`, Secs. 2.1 and 3.1; EV009–EV010 | supported |
| Lunar layers are preprocessed into immutable travel-time, energy, risk and shadow attributes, while the paper displays distance but not unsupported mixing coefficients | `src/lunar_ice_bpc/domain/real_maps.py::_path_metrics`; manuscript (1) and adjacent scope paragraph | supported |
| Core trip-level flow, activation, task count and uniqueness, binary domains, elementarity, time propagation, resource limits, recharge and trip sequencing are explicit compact equivalents of feasible-column and native-label semantics | `src/lunar_ice_bpc/exact/solver/gurobi_compact.py`; `src/lunar_ice_bpc/exact/core/columns.py`; `native/lunar_spprc/src/native_pricer.cpp`; manuscript (4a)–(7) | supported |
| Exactness is restricted to the frozen fixed logical-path solution space | `CODEX_lunar_gat_bpc_exact_algorithm_design.md`, Sec. 2.1; `plan/01_B0_Direct_DP_Frozen_Oracle.md`; EV009; CL005 | supported |
| Trip timing, recharge, energy, capacity, shadow, and horizon feasibility follow the implemented transitions | `src/lunar_ice_bpc/exact/core/columns.py`; EV002 | supported |
| The implementation computes service risk as \(0.01\theta_i\sigma_i\); the manuscript represents the resulting value as the frozen input \(\rho_i^{\mathrm{srv}}\), and operating cost is service cost plus path distance plus energy proxy | `src/lunar_ice_bpc/exact/core/columns.py`; `src/lunar_ice_bpc/exact/core/objective.py`; manuscript (6b) | supported with implementation-to-model abstraction |
| A multi-trip route is a task-disjoint, time-compatible ordered trip schedule for one rover | `CODEX_lunar_gat_bpc_exact_algorithm_design.md`, Sec. 3.3; `src/lunar_ice_bpc/exact/core/journey.py`; CL003 | supported |
| The official manuscript-wide objective is normalized operating cost plus normalized risk plus 0.4 times normalized science-weighted completion time | `src/lunar_ice_bpc/exact/core/objective.py`; EV002–EV003; CL002 | supported |
| Objective references are positive sums of componentwise feasible single-task reference values with a tracked fallback for infeasible singleton construction | `src/lunar_ice_bpc/exact/core/objective.py::objective_references`; manuscript (9) | supported |
| The configured completion weight is 0.4 and makespan is reporting-only | `src/lunar_ice_bpc/exact/core/data.py`; `src/lunar_ice_bpc/exact/core/objective.py`; EV003; CL002 | supported |
| The multi-trip route master enforces exact task coverage and a fleet limit | `CODEX_lunar_gat_bpc_exact_algorithm_design.md`, Sec. 3.5; `src/lunar_ice_bpc/exact/master/journey_rmp.py`; CL003 | supported |
| Reduced cost contains task-cover, fleet-limit, and active deterministic-cut dual contributions | `CODEX_lunar_gat_bpc_exact_algorithm_design.md`, Sec. 3.6; `src/lunar_ice_bpc/exact/master/journey_rmp.py`; EV006; CL004 | supported |
| Branch restrictions are feasibility context rather than dual terms | EV002, EV005–EV006; blueprint P09 | supported |

## Reviewer-Facing Self-Review

| Check | Finding | Resolution |
|---|---|---|
| Clarity | Path option, trip, and multi-trip route could otherwise be conflated | Each term is defined before reuse and contrasted explicitly |
| Flow | The model could jump from graph data directly to the master problem | The section follows graph → path option → trip → multi-trip route → cost → master → reduced cost |
| Terminology | Scope language must not use `universe` or imply continuous-path optimality | Uses fixed logical-path solution space and path-option space |
| Classical constraints | Reviewers may read the absence of trip-level rows in the route master as an omission | Eqs. (4a)–(7) display all defining families and Section 4.3 maps them to feasible-column/native-label enforcement |
| Coefficient calibration | Numerical mixing weights could be mistaken for scientifically calibrated lunar mobility/risk parameters | They are removed from the optimization formulation and retained only in frozen generator source/configuration |
| Notation typography | Variable indices and fixed descriptive labels could be visually conflated | Changing indices are italic; fixed labels/acronyms/operators are upright under the Elsevier notation policy |
| Objective consistency | Instance/generator payloads retain legacy alpha/beta/gamma/delta fields, while current P0V2 BPC executes the normalized objective | Scratch text follows the executed normalized objective; legacy fields remain internal and are forbidden in manuscript-facing text |
| Unsupported claims | Map fidelity and learning effectiveness are not established in this section | Both are explicitly excluded from the mathematical claim |
| Proof language | No diagnostic or heuristic statement is described as a proof | Section 3 defines scope and equations only; proof production is deferred to Section 4 |
| Missing evidence | No missing experimental value is required to state the formulation | Instance-specific values are deferred to the experimental section |

## Current Synchronization Checks

1. The equation register maps all 25 displayed manuscript tags, including
   subequations (4a), (4b), (6a), and (6b), to live source anchors.
2. Section 3 uses the base sequence (1)--(13), with grouped subequations, and
   balanced MathJax delimiters.
3. The sole objective remains normalized operating cost + normalized risk +
   \(0.4\) times normalized science-weighted completion.
4. Uncalibrated generator mixing coefficients are not displayed as
   optimization-model equations.
5. All defining route-local MILP families are explicit in Eqs. (4a)--(7) and
   are bound to feasible-column/native-SPPRC enforcement.
6. The notation register applies italic variables/changing indices and upright
   fixed labels consistently.
7. Final figures, external-citation passage checks, LaTeX labels, and Word
   conversion remain later production-stage work.
