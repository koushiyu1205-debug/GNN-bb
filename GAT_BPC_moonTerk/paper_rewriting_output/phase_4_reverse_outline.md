# Phase 4 Reverse Outline

## Reading Logic

The working draft follows a continuous argument even though the learning
experiments are not yet available: operational need leads to a fixed
logical-path optimization model; the model leads to exact BPC; learning is
inserted only as ordering; exact-safety tests precede performance claims; the
current evidence establishes the exact framework and its limits; future rows
are already allocated without predetermining their conclusions.

## Paragraph-Level Argument and Evidence Allocation

| Unit | Paragraph Function | Evidence or Citation | Maturity | Link to Next Unit |
|---|---|---|---|---|
| Title | Name the application, learning role, and exact algorithm class without claiming speedup | Confirmed motivation | `DESIGN` | Opens the application-algorithm pairing |
| Abstract A1 | State the coupled multi-trip lunar fleet-routing problem across shadowed cold-trap candidates and surrounding access terrain | C054, C055; EV010--EV011, EV032 | `SUPPORTED` | Motivates a mission-level transportation model without claiming exclusive PSR water occurrence |
| Abstract A2 | State the formulation, objective, and exactness scope | EV002--EV003, EV009; EQ-05 | `SUPPORTED` | Defines what exact optimization means |
| Abstract A3 | Separate pricing guidance, branch ranking, and proof-producing logic | EV004--EV008 | `DESIGN + PROOF CONTRACT` | Establishes the central algorithmic boundary |
| Abstract A4 | Report current exact evidence and reserve learned-performance sentence | EV014--EV025; `TBD-ABS-RESULT` | `SUPPORTED + TBD` | Prevents fabricated learning conclusions |
| 1 P1 | Distinguish remotely detected lunar water-related signals from the in-situ evidence needed to characterize a candidate site's abundance, physical occurrence and accessibility | C054, C061, C062; EV026; CL038; LS11 | `SUPPORTED CONTEXT, BOUNDED` | Opens with the scientific task gap and ends at the paper's candidate-site planning input |
| 1 P2 | Explain how PSRs, rims and transition terrain create competing time, energy, risk and cumulative-shadow path considerations | C042, C054, C055; EV011, EV029, EV032; LS01--LS02, LS07 | `SUPPORTED CONTEXT + BENCHMARK MODEL` | Converts lunar environmental context into the route-feasibility problem |
| 1 P3 | Build from heterogeneous tasks and repeated depot returns to the coupled fleet decision and the normalized science-weighted objective | C022, C025; EV001--EV003; LS05--LS08 | `SUPPORTED` | Defines what the fleet planner must decide before stating benchmark scale |
| 1 P4 | State the common 50 km by 50 km region and configured mobility regime as forward-looking benchmark assumptions | EV010--EV011, EV032; LS03--LS04 | `SUPPORTED, BOUNDED` | Separates scenario scale from current hardware performance |
| 1 P5 | Separate environmental preprocessing from static multi-path fleet optimization and restrict exactness to the fixed logical-path solution space | C041, C042, C044; EV009, EV029; LS05, LS09 | `SUPPORTED` | Prevents a time-dependent-travel overclaim and leads to route decomposition |
| 1 P6 | Explain why one multi-trip route column is the right decomposition unit and why task-plus-path resource extension makes pricing the main burden | C021, C028--C030; EV002, EV029--EV030 | `SUPPORTED` | Identifies the technical bottleneck targeted by learning |
| 1 P7 | Position learned/selective solver control while retaining exact completion, branching, cuts, bounds and tree closure on the exact path | C001, C002, C009, C059; EV001, EV004--EV008 | `SUPPORTED CONTEXT + DESIGN` | Defines the learned-action and proof-responsibility boundary |
| 1 P8--P9 | State the scoped research question, four contributions, open learning-evidence boundary and paper organization | CL001--CL011, CL035--CL038; EV025, EV027 | `MIXED, QUALIFIED` | Previews formulation, proof, guidance, evaluation and limitations |
| 2.1 P1--P3 | Position lunar path planning, mission constraints, and scientific targeting | C041, C042, C044, C054, C055 | `SUPPORTED CONTEXT` | Shows the gap at fleet-route level |
| 2.2 P1--P3 | Position route-based exact methods and selective pricing | C020, C021, C023, C028--C030, C059--C060 | `SUPPORTED CONTEXT` | Establishes exact-method precedents |
| 2.3 P1--P3 | Position learned branching and pricing while excluding learned proof authority | C001--C003, C008--C009 | `SUPPORTED CONTEXT + DESIGN` | Leads to the responsibility split |
| 3 opening--3.1 P5 | Define the 50 km by 50 km forward-looking benchmark, candidate-site/service roles, logical nodes and typed path options; display distance in manuscript (1); trace lunar terrain/illumination summaries to immutable stored attributes without displaying uncalibrated mixing weights; and prove same-endpoint path-option dominance by componentwise substitution | EV009--EV011; EV029, EV032; `domain/real_maps.py::_path_metrics`; Native option filter; LS03--LS05 | `SUPPORTED GENERATOR + SCENARIO + SCOPE BOUNDARY` | Establishes how lunar layers enter an exact dominance-reduced discrete state space without implying current hardware capability or physical calibration |
| 3.1 P6 | Distinguish the one-rover route universe \(\mathcal R(\mathcal I)\) from the fleet-schedule solution space \(\Omega(\mathcal I)\), then state fixed logical-path exactness and physical-model limits | EV009, EV029, EV031 | `SUPPORTED BOUNDARY` | Prevents both route/fleet type ambiguity and continuous-terrain overclaim |
| 3.2 P1--P4 | Connect repeated depot deployment to trip feasibility; state the nonrestrictive \(\bar S=|\mathcal T|\) slot bound; define trip sequences in (2)--(3); then state core trip-level flow, activation, task-count/uniqueness, domain, elementarity, temporal, resource, recharge and sequencing families in (4a)--(7) | EV002--EV003; EV029, EV032; `gurobi_compact.py`; `core/columns.py`; Native SPPRC; LS06--LS07 | `SUPPORTED` | Defines a complete feasible multi-trip route column and distinguishes hard shadow feasibility from objective risk |
| 3.2 P5 | Aggregate trips into multi-trip routes and incidence coefficients in manuscript (8) | EV002--EV003 | `SUPPORTED` | Supplies master variables |
| 3.3 P1--P3 | Define componentwise single-task normalizers and the sole objective in manuscript (9)--(10), then exclude makespan through (11) | EV003, EV028; `core/objective.py` | `SUPPORTED` | Fixes all column and master costs |
| 3.3 P3--P4 | State the multi-trip route master and reduced cost under dual/cut/branch context | EV004--EV006; EQ-08--EQ-10 | `SUPPORTED` | Opens the exact BPC method |
| 4.1 P1--P5 | Establish pricing as the operational core that assembles lunar task/path/resource decisions; assign learning to ordering and exact logic to bounds, proof, cuts and branching validity; formalize proof-gated node pruning in manuscript (14) | EV001, EV004--EV008, EV032; node-bound proof record; LS06--LS10 | `DESIGN + PROOF CONTRACT` | Provides the responsibility architecture and prevents diagnostic-bound pruning |
| 4.1 Algorithm 1 | Make the node workflow auditable from RMP/Phase I through pricing, deterministic separation, bound use, and branching | EV004--EV008; S016--S023 | `DESIGN + IMPLEMENTED EXACT SHELL` | Calls the two guidance components without delegating any proof-bearing conclusion |
| 4.2 | Explain RMP lifecycle, column identity, objective closure and addability-aware negative harvest in manuscript (15) | EV003--EV005; `pricing/harvest.py` | `IMPLEMENTED` | Produces duals and admits only audited addable negatives while guidance changes order only |
| 4.3 P1--P7 | Map (4a)--(7) to native transition invariants, visited masks and resource states, then explain exact resource pruning, path-option substitution, guarded label dominance, completion-bound pruning and exhaustive no-negative completion in (16)--(19) | EV004--EV005, EV029--EV031; `gurobi_compact.py`; native pricer; `completion_bounds.py` | `IMPLEMENTED WITH CONTEXT GUARDS` | Shows that the dominance-reduced pricing representation remains exact and defines the primary learned-guidance target |
| 4.4 | Introduce SRI-3 as a task-triple subset-row inequality, explain its route coefficient, derive validity, root violation and deterministic retention in manuscript (20)--(21), then prohibit learned cut control and nonroot separation | EV006, EV015--EV018; `cuts.py`; `live_sri.py` | `IMPLEMENTED, ROOT-ONLY` | Makes the valid inequality understandable before separating mathematical validity from empirical performance and learning |
| 4.5 | Define Ryan--Foster co-occurrence/fractionality in manuscript (22), exact children, deterministic order and fallback | EV007; `branch_probe.py` | `IMPLEMENTED EXACT SHELL + DIAGNOSTIC ORDER` | Defines the secondary learned target without treating no-pair as integrality |
| 4.6.1 | Define graph state and typed pricing/branch outputs | EV008; M002--M003 | `DESIGN; ARTIFACTS TBD` | Specifies trainable interfaces |
| 4.6.2 | Describe pricing ordering, immediate registration of every delayed item, exact fallback and the unresolved deferred-pricing condition in manuscript (23) | EV004--EV005, EV008; proof-debt implementation queue | `DESIGN + EXACT SHELL` | Makes pricing the main learning action while any delayed item remains visible until resolved |
| 4.6.2 Algorithm 2 | Convert optional pricing hints into set-preserving order, true-RC audit, resolution of deferred work, and native exact completion | EV004--EV005, EV008; M002 | `DESIGN + EXACT SHELL; CHECKPOINT TBD` | Shows why only exact completion may prove no-negative-reduced-cost closure |
| 4.6.3 | Describe branch ranking after exact-valid candidate construction | EV007--EV008 | `DESIGN + EXACT SHELL` | Makes branching an incremental action |
| 4.6.3 Algorithm 3 | Rank a deterministically bounded exact-valid candidate set, construct both exact children, and fail closed when fallback is unavailable | EV007--EV008; M003 | `DESIGN + EXACT SHELL; CHECKPOINT TBD` | Preserves candidate validity and branch completeness independently of learning |
| 4.7 | Prove canonical-route completeness, master/fleet equivalence, exact node-LP closure, SRI/branch preservation, guidance invariance, and tree-level optimality; distinguish sound exact conclusions from incomplete termination | EV002, EV004--EV009, EV025, EV029--EV031 | `CONDITIONAL MATHEMATICAL PROOF` | Establishes the exactness of the complete algorithm and converts every assumption into an audit gate |
| 5.1 | Register RQ1--RQ5 without presupposing improvements | EV027, EV033 | `PROTOCOL` | Organizes learning and four-phase seasonal comparisons |
| 5.2 | Define the 120-instance corpus and map provenance, then reserve the paired 12-anchor design grouped into four south-polar phases | EV010--EV011, EV033; C063; M006 | `SUPPORTED + TBD` | Establishes current evaluation units without relabeling them as seasonal evidence |
| 5.3 | Reserve split/leakage manifest | M001 | `TBD` | Prevents premature generalization |
| 5.4 | Define L0, L1, L2 and exact comparators | EV014, EV027; C059 | `PROTOCOL` | Isolates pricing then branch effects |
| 5.5 | Reserve trained-model configurations | M002--M003 | `TBD` | Blocks untraceable implementation claims |
| 5.6 | Put proof equivalence and fallbacks before speed | EV004--EV008, EV027 | `SUPPORTED PROTOCOL` | Defines pass/fail safety endpoints |
| 5.7 | Define workload, performance, and uncertainty fields | M004 | `PROTOCOL + TBD RUN PLAN` | Determines the future result schema |
| 5.8 | Define held-out and out-of-distribution evaluation | M005 | `PROTOCOL + TBD` | Determines robustness evidence |
| 6.1 | Report 5/10/20/30 exact no-cut baseline rows | EV014 | `FROZEN RESULT` | Establishes the control and scale trend |
| 6.2 | Report formal SRI correctness and non-promotion | EV015--EV018 | `FROZEN RESULT, NOT PROMOTED` | Demonstrates evidence-gate discipline |
| 6.3 | Report exact state compression and diagnostic timing with labels intact | EV019--EV021 | `FROZEN + DIAGNOSTIC` | Shows exact-engine work distinct from learning |
| 6.4 | Reserve L0/L1/L2/G result blocks and figures | M004--M005; EXP-L0/L1/L2/G | `TBD` | Leaves performance conclusion genuinely open |
| 6.5 | Reserve paired seasonal operating-phase results using normalized science-weighted completion time and reporting-only makespan | EV033; M006; EXP-EPOCH | `TBD` | Tests the environmental design without changing the exact solver or claiming a universal best season |
| 6.6 | Report scale-50/100 legal incomplete, fail-closed behavior | EV022--EV025 | `FROZEN BOUNDARY` | Defines the present resource limit |
| 7.1 | State only current answers and reserve RQ1--RQ5 answers | EV014--EV025, EV033; EXP rows | `SUPPORTED + TBD` | Separates known and unknown conclusions |
| 7.2 | Explain the pricing-primary/branch-secondary allocation | Method contract; C001--C003, C059 | `DESIGN RATIONALE` | Connects algorithm design to workload |
| 7.3 | Bound transportation implications and reserve measured implication | EV009--EV011; M004--M005 | `SUPPORTED BOUNDARY + TBD` | Avoids field-performance inference |
| 7.4--7.6 | State proof, data, environmental, computational, and empirical limits | EV009--EV011, EV022--EV027 | `SUPPORTED LIMITATIONS` | Calibrates conclusion scope |
| 7.7 | Define evidence-driven learning work and rolling epoch update/replanning extensions | M001--M006; C063 | `TBD ROADMAP` | Preserves per-instance exactness while withholding a global adaptive-policy claim |
| 8 | Conclude the formulation and exact framework; state that learning benefit is not established | CL001--CL005, EV014--EV025, EV027 | `SUPPORTED` | Closes at present maturity |
| Appendices A–D | Preserve notation, proof conditions, SRI boundary, exploratory evidence, and resource boundary | EQ register; EV015–EV025 | `SUPPORTED` | Makes scope auditable |
| Appendix E | List the missing learning and seasonal-phase artifact packages | M001--M006 | `TBD LEDGER` | Defines what later evidence must supply |

## Continuity Verdict

No missing experiment removes a logical step. The draft explains why the
problem matters, what is optimized, how exactness is retained, how learning
would be tested, what has already been demonstrated, and which conclusions
remain unavailable.
