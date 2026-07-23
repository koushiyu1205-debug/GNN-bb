# Section 3 Draft Audit

## Draft Scope

- Manuscript unit: Section 3, *Problem Setting and Mathematical Formulation*
- Draft file: `manuscript_draft.md`
- Draft language: English
- Draft date: 2026-07-23
- Blueprint rows executed: P01–P09
- Learning-performance claims: none

## Compact Outline

1. Define the directed logical transportation network and task attributes.
2. Define the three declared path options and the fixed logical-path solution
   space.
3. Separate mathematical exactness from map and physical fidelity.
4. Define timed, resource-feasible depot-to-depot sorties.
5. Define multi-sortie rover journeys and exact task-incidence coefficients.
6. State the normalized additive objective and the reporting-only makespan.
7. Formulate the integer journey master and its restricted LP.
8. Derive the shared reduced-cost expression.
9. Keep branch restrictions as feasibility context rather than dual terms.

## Reverse Outline

| Unit | Paragraph Role | Topic-Sentence Test | Dependency Check | Status |
|---|---|---|---|---|
| S3-OPEN | Scope and terminology | Opens by naming the transportation decisions represented by the model | Introduces path option, sortie, and journey before symbols | PASS |
| P01 | Network and task inputs | Opens with task, rover, depot, and graph notation | Supplies entities used in all later equations | PASS |
| P02 | Path-option space | Opens with the finite option set on each directed edge | Supplies movement attributes used in sortie construction | PASS |
| P03 | Exactness scope | Opens with an explicit discrete-scope statement | Bounds all later optimality language | PASS |
| P04-A | Sortie sequence and timing | Opens by defining a depot-to-depot sortie | Timing recurrence follows declared path choices | PASS |
| P04-B | Sortie resources and feasibility | Opens with return/recharge construction | Feasibility uses only implemented resources | PASS |
| P05 | Journey column | Opens by defining a one-rover multi-sortie schedule | Separates journey, sortie, and path option | PASS |
| P06 | Official objective | Opens with the three official additive quantities | Matches the current normalized objective implementation | PASS |
| P07 | Makespan boundary | Opens by excluding makespan from the objective | Prevents incompatible objective transfer | PASS |
| P08 | Integer journey master | Opens with the feasible column set and decision variable | Task cover, fleet, and deterministic-cut rows match the model contract | PASS |
| P09 | Restricted master and reduced cost | Opens with the LP relaxation and pricing relation | One expression serves pricing, admission, and audit | PASS |

## Claim–Evidence Map

| Claim | Evidence | Status |
|---|---|---|
| Tasks, rover capacity, time windows, service resources, and directed path-option attributes are instance inputs | `src/lunar_ice_bpc/exact/core/data.py`; EV010–EV011 | supported |
| The current benchmark declares three path alternatives per directed logical edge | `CODEX_lunar_gat_bpc_exact_algorithm_design.md`, Secs. 2.1 and 3.1; EV009–EV010 | supported |
| Exactness is restricted to the frozen fixed logical-path solution space | `CODEX_lunar_gat_bpc_exact_algorithm_design.md`, Sec. 2.1; `plan/01_B0_Direct_DP_Frozen_Oracle.md`; EV009; CL005 | supported |
| Sortie timing, recharge, energy, capacity, shadow, and horizon feasibility follow the implemented transitions | `src/lunar_ice_bpc/exact/core/columns.py`; EV002 | supported |
| A journey is a task-disjoint, time-compatible multi-sortie schedule for one rover | `CODEX_lunar_gat_bpc_exact_algorithm_design.md`, Sec. 3.3; `src/lunar_ice_bpc/exact/core/journey.py`; CL003 | supported |
| The official objective is normalized operating cost plus normalized risk plus weighted normalized completion | `src/lunar_ice_bpc/exact/core/objective.py`; EV002–EV003; CL002 | supported |
| The configured completion weight is 0.4 and makespan is reporting-only | `src/lunar_ice_bpc/exact/core/data.py`; `src/lunar_ice_bpc/exact/core/objective.py`; EV003; CL002 | supported |
| The journey master enforces exact task coverage and a fleet limit | `CODEX_lunar_gat_bpc_exact_algorithm_design.md`, Sec. 3.5; `src/lunar_ice_bpc/exact/master/journey_rmp.py`; CL003 | supported |
| Reduced cost contains task-cover, fleet-limit, and active deterministic-cut dual contributions | `CODEX_lunar_gat_bpc_exact_algorithm_design.md`, Sec. 3.6; `src/lunar_ice_bpc/exact/master/journey_rmp.py`; EV006; CL004 | supported |
| Branch restrictions are feasibility context rather than dual terms | EV002, EV005–EV006; blueprint P09 | supported |

## Reviewer-Facing Self-Review

| Check | Finding | Resolution |
|---|---|---|
| Clarity | Path option, sortie, and journey could otherwise be conflated | Each term is defined before reuse and contrasted explicitly |
| Flow | The model could jump from graph data directly to the master problem | The section follows graph → path option → sortie → journey → cost → master → reduced cost |
| Terminology | Scope language must not use `universe` or imply continuous-path optimality | Uses fixed logical-path solution space and path-option space |
| Objective consistency | The older design document contains an obsolete alpha/beta/gamma/delta cost sketch | Draft follows the current normalized objective implementation and records makespan as reporting-only |
| Unsupported claims | Map fidelity and learning effectiveness are not established in this section | Both are explicitly excluded from the mathematical claim |
| Proof language | No diagnostic or heuristic statement is described as a proof | Section 3 defines scope and equations only; proof production is deferred to Section 4 |
| Missing evidence | No missing experimental value is required to state the formulation | Instance-specific values are deferred to the experimental section |

## Open Items Before Final LaTeX

1. Assign final equation and cross-reference labels.
2. Insert the approved logical-network/path-option figure and notation table.
3. Confirm target-journal notation styling and equation punctuation.
4. Add external map-source citations only after final citation-key verification.
