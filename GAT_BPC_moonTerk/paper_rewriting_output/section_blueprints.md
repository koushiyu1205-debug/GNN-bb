# Section Blueprints

## Blueprint Status

- Workflow: `build_from_materials`
- Scene: journal article
- Target: *Transportation Research Part C: Emerging Technologies*
- Output language: English
- Controlling motivation: pricing-led, branching-assisted learning guidance
  inside an exact Branch-Price-and-Cut framework for lunar water-ice
  exploration fleet routing.
- Drafting permission: Phase 4 was explicitly authorized and is complete as an
  English working draft. Blueprint rows now serve as the audit plan for
  `manuscript_draft.md`; missing learning artifacts/results remain `TBD`.
- Prior Section 3 prose: archived as `section_3_pre_phase4_scratch.md`. The
  active Section 3 was rebuilt after the equation and objective freeze.
- Evidence cutoff: 2026-07-23 (Asia/Shanghai)

## Working Title and Throughline

### Preferred working title

**Learning-Guided Exact Branch-Price-and-Cut for Multi-Trip Lunar
Water-Ice Exploration Routing**

### Alternate title

**Pricing-Led Learning Guidance in Exact Branch-Price-and-Cut for
Resource-Constrained Lunar Exploration Routing**

### Title constraints

- Show both the transportation problem and the solution class.
- Do not include a speedup, solved scale, “first,” “novel,” or trained-GAT
  claim.
- Keep “proof-preserving” only if the final method and experiments retain
  the exact fallback and audit evidence specified below.

### Whole-paper planned claim

The planned paper formulates a fixed logical-path solution space,
resource-constrained, multi-trip lunar fleet-routing problem and develops an
exact BPC architecture in which learned policies prioritize pricing effort and
rank valid branch candidates, while exact pricing completion, deterministic
cut logic, branch validity/completeness, bounds, pruning and proofs remain
exclusively on the exact path.

This is a method-and-validation claim. It is not yet a learning-performance
claim.

## Evidence Maturity Codes

| Code | Meaning | Drafting Rule |
|---|---|---|
| `NOW-PROOF` | Mathematical or implementation contract is available | May be drafted with its assumptions and fixed logical-path solution space scope |
| `NOW-FROZEN` | Frozen machine-readable experiment is available | May report only the recorded design and values |
| `NOW-BOUNDARY` | Negative, incomplete, benchmark-only or diagnostic evidence is available | Qualifier must appear next to the claim |
| `DESIGN` | Confirmed algorithm design or implemented scaffold exists | Use “proposed,” “designed,” or “is intended to”; no effectiveness verb |
| `TBD-RESULT` | Required learning evidence is absent | Define protocol/table shell only; do not write a conclusion |
| `CITATION` | External contextual claim | Cite a verified source; never use it as project-result evidence |

## Provisional Length and Visual Budget

The target journal's current author-guide length limits were not verified in the
research client. The following is a revisable planning budget, not a submission
rule.

| Manuscript Part | Planned Words | Planned Visuals |
|---|---:|---|
| Abstract and keywords | 220–280 | none |
| 1. Introduction | 1,100–1,300 | none |
| 2. Related work | 1,200–1,500 | optional taxonomy table |
| 3. Problem setting and formulation | 1,400–1,700 | FIG01 or FIG06; TAB01–TAB03 |
| 4. Proposed exact learning-guided BPC | 2,600–3,100 | FIG09–FIG11 |
| 5. Experimental design | 1,300–1,700 | experiment matrix |
| 6. Computational results | 1,700–2,200 | FIG12, FIG15–FIG16; TAB04, TAB08 |
| 7. Discussion and limitations | 900–1,200 | none |
| 8. Conclusion | 250–400 | none |
| Appendices | as needed | FIG13–FIG14; TAB05–TAB07 |

## Paper-Level Argument Architecture

| Stage | Reader Question | Section Answer | Controlling Evidence |
|---|---|---|---|
| Need | Why is this a transportation optimization problem rather than only local rover navigation? | Coupled fleet assignment, sequencing, resource, risk and temporal decisions govern mission-level movement | EV001, EV010, EV011; C025, C041, C042, C054, C055 |
| Gap | Why are existing lunar planners and exact-routing methods insufficient for the intended claim? | Lunar planning largely addresses waypoint/path generation, while exact BPC is computationally demanding and learning precedents do not remove the need for proofs | C001, C002, C020, C021, C041–C045 |
| Model | What exactly is optimized and where does exactness apply? | Multi-trip route columns over a fixed logical graph with three path options per directed edge | EV002, EV003, EV009, EV010 |
| Method | What does learning control, and what remains exact? | Learning orders pricing work and valid branch candidates; deterministic exact logic owns cuts, completeness, proof and proofs | EV001, EV004–EV008 |
| Evidence | What must be tested before the method can claim value? | Exact equivalence first, then pricing ablation, incremental branch ablation, overhead/fallback and held-out behavior | EV027; EXP-L0/L1/L2/G |
| Interpretation | What does the evidence mean for fleet planning, and what does it not mean? | Translate validated solver behavior into planning reliability while preserving map, fixed logical-path solution-space, scale and data limits | EV009–EV011, EV025; C039, C052–C055 |

## Planned Core Citation Set

The following 20 candidates are locked in `citation_lock.md`. Metadata/source
verification has been completed at the level recorded there; sentence-level
passage verification and final citation-key export remain mandatory before
insertion.

| Role | Candidate IDs |
|---|---|
| Lunar application and mission constraints | C041, C042, C044, C054, C055 |
| Transportation-system and complex-fleet framing | C022, C025 |
| Exact route-based/BPC precedents | C020, C021, C023, C028, C029, C030, C060 |
| Learning-guided exact search and pricing | C001, C002, C003, C008, C009 |
| Non-learning pricing-control baseline | C059 |

Reserve sources C043, C045, C046, C052 and C053 may replace or supplement the
core set if a specific sentence requires their narrower support.

# Front Matter Blueprint

| Unit | Planned Function | Evidence/Citation Anchor | Maturity | Guardrail |
|---|---|---|---|---|
| TITLE | Join the lunar fleet-routing problem to proof-preserving learning-guided exact BPC | EV001; style profile | DESIGN | No speedup, “first,” solved-scale or trained-model signal |
| ABS-1 | State the operational fleet-routing problem and coupled constraints | EV010, EV011; C041, C042, C055 | CITATION | Do not imply field deployment or physical validation |
| ABS-2 | State the fixed logical-path solution space multi-trip route formulation and exact BPC framework | EV002–EV006, EV009 | NOW-PROOF | Include fixed logical-path solution space scope |
| ABS-3 | State the pricing-led and branching-assisted learned actions | EV001, EV007, EV008 | DESIGN | Learning ranks work/candidates; it does not prove or control cuts |
| ABS-4 | State the exactness contract | EV004, EV005, EV007 | NOW-PROOF | Exact completion and fallbacks remain mandatory |
| ABS-5 | Reserve the numerical result sentence | EV027; EXP-L0/L1/L2/G | TBD-RESULT | No result wording until frozen learning evidence exists |
| ABS-6 | State a bounded implication and limitation | EV009–EV011 | DESIGN | No continuous-terrain or scientific-yield claim |
| KEYWORDS | Use 5–7 searchable terms | lunar exploration routing; multi-trip fleet routing; branch-price-and-cut; resource-constrained shortest path; learning-guided optimization; exact algorithms | DESIGN | Avoid “learning to cut” |

# 1. Introduction Blueprint

## Section purpose

Move from a transportation-system consequence to one precise algorithmic gap.
The section must make the learning/exact split inevitable before presenting the
contribution list.

| Unit | Paragraph Function | Evidence/Citation Anchor | Visual | Maturity | Guardrail |
|---|---|---|---|---|---|
| INT-1 | Open with the gap between remotely detected water-related signals and the in-situ evidence needed to characterize candidate sites, then define detection, sampling and drilling as the planning task | C054, C061, C062; EV026; LS01--LS02 | none | CITATION | Chang'E-5 samples support heterogeneous occurrence and retention factors, not south-pole abundance or accessibility |
| INT-2 | Explain low solar elevation, PSRs, thermal burden, static task windows, no task-site waiting, depot departure adjustment, cumulative shadow exposure and alternative-path trade-offs as one lunar operating problem | C042, C054, C055; EV029, EV032, EV034, EV035; LS01--LS02, LS07, LS13--LS14 | none | CITATION + DESIGN-ONLY | Direct sunlight is not a service prerequisite; communication remains exogenous; task-site waiting is prohibited; depot waiting counts toward mission time; shadow exposure, energy and risk remain distinct |
| INT-3 | Define the heterogeneous multi-path, multi-trip capacitated routing decision, constraints and normalized objective; identify the locally available LOLA-derived inputs and qualify the forward-looking regional benchmark | EV001--EV003, EV009--EV011, EV032; LS03--LS09 | none | MIXED | Use elevation, slope, roughness, PSR and average solar-visibility raster provenance; 50 km by 50 km and 30 km/h are scenario assumptions |
| INT-4 | Explain the representation loss from a single inter-site path, the route-column pricing burden and the distinction between learned work ordering and proof-producing exact completion | C001, C002, C009, C021, C028--C030, C059; EV002, EV004--EV008, EV030 | none | CITATION + DESIGN | Do not claim an observed learning effect or imply that a score proves pricing closure |
| INT-5 | Present pricing-led, branch-assisted exact BPC, deterministic cuts, mandatory exact fallback, per-epoch solving and fixed-path exactness scope | EV004--EV009, EV033; CL005--CL011, CL035, CL039 | none | NOW-PROOF + TBD-EVIDENCE | No self-posed research question; no learning control of cuts; no cross-epoch route-robustness or continuous-path claim |
| INT-6 | State three contributions—model, algorithm, and benchmark/evaluation package—and the section order in one closing paragraph | CL001--CL011, CL035--CL042; EV002--EV011, EV027--EV037 | none | MIXED | The algorithm contribution combines the conditional proof and learning interface; the frozen no-task-wait baseline is established, while learning and phase effects remain open |

## Introduction exit condition

The reader should be able to state: (i) the transportation decision, (ii) the
fixed logical-path solution space exactness scope, (iii) why pricing is the primary learned target,
(iv) why branch ranking is secondary, and (v) why cuts and proofs remain
deterministic.

# 2. Related Work Blueprint

## 2.1 Lunar mission planning

| Unit | Paragraph Function | Citation Anchor | Maturity | Guardrail |
|---|---|---|---|---|
| RW-1 | Organize lunar work by local navigation, safe access to shadowed candidate regions, illumination-aware path-network construction and fleet-level prospecting decisions | C041, C042, C044, C054, C055; LS01--LS05 | CITATION | Taxonomy only; do not state that all lunar water occurs in PSRs |
| RW-2 | Identify the unfilled formulation space: exact multi-trip fleet assignment and route selection over predeclared path alternatives | C041, C044, C049; EV009, EV010 | CITATION + NOW-PROOF | Present as a scoped contrast, not universal absence |
| RW-3 | Connect terrain/illumination/map provenance to optimization inputs and later limitations | C044, C052, C053, C055; EV011 | CITATION | Derived resource/risk maps are not direct ice ground truth |

## 2.2 Exact routing algorithms

| Unit | Paragraph Function | Citation Anchor | Maturity | Guardrail |
|---|---|---|---|---|
| RW-4 | Explain how structured multi-trip route columns encode internal resource processes | C021, C029, C030 | CITATION | Use precedents for structure, not project validation |
| RW-5 | Position tailored SPPRC pricing, valid inequalities and branching as standard proof-bearing BPC components | C020, C023, C028, C060 | CITATION | Do not claim BPC/SRI as novel by themselves |
| RW-6 | Distinguish selective/stabilized pricing schedules from exact pricing termination | C059 and reserve C027 | CITATION | Pricing control is a baseline; exact completion remains separate |

## 2.3 Learning-guided optimization

| Unit | Paragraph Function | Citation Anchor | Maturity | Guardrail |
|---|---|---|---|---|
| RW-7 | Summarize foundational and recent learning-to-branch work, ending with exact vehicle-routing BPC precedent | C056, C057, C003, C001 | CITATION | C001 blocks any “first learning-guided exact BPC” claim |
| RW-8 | Summarize learned pricing/column-generation control and identify exact fallback as the unresolved proof production requirement for this paper | C002, C009, C059 | CITATION | Learned column discovery cannot prove exhaustion |
| RW-9 | Delimit the excluded learned-cut direction | C004, C006, C007 or C058; EV001, EV006, EV007 | CITATION + NOW-PROOF | One concise boundary paragraph; do not create a learned-cut contribution |
| RW-10 | Close with the paper-specific integration gap and evaluation burden | SOTA gap map; EV001, EV027 | DESIGN | Gap is application/interface/validation-specific, not a universal novelty claim |

# 3. Problem Definition and Mathematical Formulation Blueprint

## 3.1 Fixed logical network and path options

| Unit | Paragraph/Model Function | Evidence Anchor | Visual/Table | Maturity | Guardrail |
|---|---|---|---|---|---|
| PROB-1 | Define the forward-looking 50 km by 50 km benchmark extent, support depot, candidate prospecting sites, rover fleet, operation modes and directed logical graph | README.md lines 147--155; `domain/scenario.py`; EV010, EV011; LS03--LS05 | FIG01; TAB02–TAB03 | NOW-PROOF | Distinguish scenario parameters and derived inputs from current rover capabilities and mission observations |
| PROB-2 | Define the epoch anchor \(b_\zeta\), mission window \(\mathcal W_\zeta\), one-hour environmental sampling and external instance index, then define three declared path options per directed edge and immutable path attributes within each window-aggregated instance | EV009, EV010, EV033; C063; CL039; M006 | FIG06 | NOW-PROOF + TBD-EVIDENCE | Hold epoch and hourly samples outside the optimizer and SPPRC state; runtime does not optimize over continuous paths or switch attributes by departure time |
| PROB-2A | Define path distance and identify the lunar terrain, epoch-window illumination, PSR, crater, steep-slope and directional-elevation inputs summarized during preprocessing | `domain/real_maps.py::_path_metrics`; manuscript (1); C063; M006 | equation block | NOW-PROOF + TBD-EVIDENCE | PSR membership is spatially fixed; transient illumination is aggregated before optimization and may differ across epochs; M006 must freeze the aggregation rule; do not display uncalibrated mixing coefficients as model equations |
| PROB-3 | State per-epoch exactness scope and modeling assumptions | EV009; CL005, CL039 | TAB01 | NOW-PROOF | Repeat fixed logical-path solution-space qualifier and state that separate epoch optima do not prove one robust or dynamically optimal plan |

## 3.2 Multi-trip route feasibility

| Unit | Paragraph/Model Function | Evidence Anchor | Visual/Table | Maturity | Guardrail |
|---|---|---|---|---|---|
| PROB-4 | Define task requirements, service modes, time windows, science weights and resource attributes | EV010; source S006 | TAB01 | NOW-PROOF | Do not invent parameter values not in manifests/config |
| PROB-5 | Define trip feasibility and reconstruction: supported-depot-only waiting, adjustable departure, arrival-equals-service-start timing, time windows, selected-arc temporal equalities, energy, shadow exposure, load, service risk, operating cost, weighted completion, recharge and trip sequencing | EV002, EV035--EV036; manuscript (2)–(7) | TAB01; equation block | IMPLEMENTED + PROVED | Derive the common feasible-departure interval; count depot delay in mission time; distinguish prescribed service from idle waiting; state the base-power/thermal-control system boundary |
| PROB-5A | Display the core trip-level MILP families: depot/task flow, activation, task-count and uniqueness links, binary domains, subtour elimination, no-wait temporal equalities, depot waiting, resource limits, recharge and inter-trip compatibility | manuscript (4a)–(7); `gurobi_compact.py`; EV035--EV036 | equation blocks | IMPLEMENTED + PROVED | These define feasible columns in \(\mathcal P(n)\), not additional route-master rows; selected-arc lower and upper temporal rows enforce arrival equals service start |
| PROB-6 | Define a multi-trip route as one rover's ordered sequence of compatible trips with recharge/docking relations | EV002; CL003 | FIG09 | NOW-PROOF | A multi-trip route is not a single trip or a local path |

## 3.3 Route-based master problem

| Unit | Paragraph/Model Function | Evidence Anchor | Visual/Table | Maturity | Guardrail |
|---|---|---|---|---|---|
| PROB-7 | Define the normalized additive objective and explain that its weighted-completion term advances completion of higher-science-weight prospecting tasks without introducing an ownership, race or makespan interpretation | EV002, EV003; CL002; manuscript (8)–(10); LS08 | TAB01; equation block | NOW-PROOF | The sole objective is normalized operating cost + normalized risk + 0.4 times normalized science-weighted completion |
| PROB-8 | State that makespan is a reporting metric, not a pricing/master objective term | EV003 | TAB01 note | NOW-PROOF | Never add makespan without a linking variable |
| PROB-9 | Present binary route variables, exact task-cover constraints and fleet-size constraint | EV002; CL003 | TAB01 | NOW-PROOF | Preserve set-partitioning equality |
| PROB-10 | Derive the route reduced cost with task, fleet and active deterministic-cut duals | EV002, EV006; CL004 | equation block | NOW-PROOF | Branch restrictions are feasibility context, not duals |

# 4. Learning-Guided Exact Branch-Price-and-Cut Framework Blueprint

## 4.1 Algorithm overview

| Unit | Paragraph Function | Evidence Anchor | Visual | Maturity | Guardrail |
|---|---|---|---|---|---|
| METH-1 | Introduce the full node loop and the two-lane heuristic/exact responsibility split | EV001, EV004–EV008 | FIG09–FIG10 | DESIGN + NOW-PROOF | No learning arrow into cut control, bounds, pruning or proofs |
| METH-2 | Define exact and incomplete outcomes through their mathematical activation conditions | EV004, EV025; source S022 | FIG11 | NOW-PROOF | Incomplete pricing cannot support a proof that no negative-reduced-cost route exists |
| METH-2A | Give the line-numbered node procedure from RMP/Phase I through pricing, deterministic separation, bound use and branching | EV004–EV008; S016–S023 | ALG01 | DESIGN + NOW-PROOF | Optional hints may reorder work but cannot determine any proof-bearing node conclusion |
| METH-2B | State the valid-bound, exact-pricing, audit, empty-debt and incumbent inequality required for node pruning | node-bound certificate; branch-tree solver; manuscript (14) | equation block | NOW-PROOF | Diagnostic or incomplete lower bounds cannot prune |

## 4.2 Restricted master problem

| Unit | Paragraph Function | Evidence Anchor | Visual | Maturity | Guardrail |
|---|---|---|---|---|---|
| METH-3 | Explain initial columns, RMP solution, true-dual extraction and column admission | EV002, EV004; S016 | FIG11 | NOW-PROOF | Use the same reduced-cost definition throughout |
| METH-4 | Explain addability-aware negative harvest, duplicate handling, new-task-set priority, pool updates and audit bindings | EV004, EV006; S016–S018; `pricing/harvest.py`; manuscript (15) | FIG11; equation block | NOW-PROOF | Guidance changes the order key only; it never changes negativity, branch/cut feasibility, uniqueness or addability |

## 4.3 Exact pricing

| Unit | Paragraph Function | Evidence Anchor | Visual/Table | Maturity | Guardrail |
|---|---|---|---|---|---|
| METH-5 | Map every route-local constraint family in (4a)–(7) to its exact label invariant, transition, resource state or visited-set rule, then define task/path/time/energy/load/shadow/risk updates | EV002, EV004; S017–S019; `gurobi_compact.py`; Native SPPRC | constraint-to-label table | NOW-PROOF | Do not duplicate the compact MILP in the pricing section; include only implemented states and transitions |
| METH-6 | Define resource pruning, guarded dominance, positive-dual completion-bound pruning, branch/cut context and exact terminal acceptance | EV004–EV006; S019–S020; native pricer; manuscript (16)–(18) | FIG11; equation block | NOW-PROOF | Disable a pruning rule outside its proved context |
| METH-7 | Separate fast/ordered pricing work from mandatory true-dual exact completion | EV004, EV007; C059 | FIG10–FIG11; ALG02 | NOW-PROOF | Only completion may prove no negative column |

## 4.4 Valid inequalities

| Unit | Paragraph Function | Evidence Anchor | Visual/Table | Maturity | Guardrail |
|---|---|---|---|---|---|
| METH-8 | Introduce SRI-3 as a subset-row inequality over a task triple, explain its binary route coefficient and integer-feasible interpretation, then derive validity, violation and deterministic retention under the predefined root policy | EV006; S021; `cuts.py`; `live_sri.py`; manuscript (20)–(21) | equation block; optional appendix algorithm | NOW-PROOF | Define the acronym before reuse; separate only at the root; descendants may inherit admitted root inequalities but generate no new SRI; do not infer speed from validity |
| METH-9 | Explain active-cut Phase-I, reduced-cost reconstruction, lineage and proof binding | EV006 | FIG11 | NOW-PROOF | Cut context must be visible to exact pricing |
| METH-10 | State the learning exclusion: no learned generation, selection, activation, retention or removal | EV001, EV006, EV007; CL009, CL027 | FIG10 | NOW-PROOF | No learned-cut ablation |

## 4.5 Branching rule

| Unit | Paragraph Function | Evidence Anchor | Visual | Maturity | Guardrail |
|---|---|---|---|---|---|
| METH-11 | Define Ryan–Foster co-occurrence, fractionality, deterministic order, same/different-route children and child feasibility | EV005; S020; manuscript (22) | FIG11; equation block | NOW-PROOF | Route membership is the branch object; ranking never changes the exact candidate set |
| METH-12 | Define fallback when no fractional Ryan–Foster pair exists | EV005; CL008 | FIG10–FIG11 | NOW-PROOF | Absence of a fractional Ryan–Foster pair is not an integrality proof |

## 4.6 Learning guidance

### 4.6.1 Graph representation

| Unit | Paragraph Function | Evidence Anchor | Visual/Table | Maturity | Guardrail |
|---|---|---|---|---|---|
| METH-13 | Specify the planned graph representation: task/path/resource features plus solver context | EV007, EV008; C003, C008 | feature table | DESIGN | Architecture/hyperparameters remain `TBD` until model artifacts exist |
| METH-14 | Define typed output heads and context/version/OOD metadata | EV007, EV008; S023–S024 | interface table | DESIGN | The current deterministic shadow-only execution path is not a trained model |

### 4.6.2 Pricing guidance

| Unit | Paragraph Function | Evidence Anchor | Visual | Maturity | Guardrail |
|---|---|---|---|---|---|
| METH-15 | Define which pricing work items may be ranked and the objective of prioritization | EV001, EV007; C002, C009, C059 | FIG09–FIG10 | DESIGN | Do not claim reduced effort before EXP-L1 |
| METH-16 | Define finite delay, the mathematical unresolved-obligation condition, and mandatory release/repricing before proof production | EV007; proof-debt implementation queue; manuscript (23) | FIG10–FIG11; equation block | NOW-PROOF + DESIGN | No permanent drop of a true-negative or unknown-RC candidate |

### 4.6.3 Branch guidance

| Unit | Paragraph Function | Evidence Anchor | Visual | Maturity | Guardrail |
|---|---|---|---|---|---|
| METH-17 | Define ranking over an exact-valid candidate set and expensive-evaluation ordering | EV001, EV005, EV007; C001, C003 | FIG09–FIG10; ALG03 | DESIGN | Learning cannot invent validity or remove fallback |
| METH-18 | Define failure/OOD behavior and deterministic candidate selection fallback | EV005, EV007 | FIG10–FIG11; ALG03 | DESIGN | No branch-performance claim before EXP-L2 |

## 4.7 Exactness proof

| Unit | Paragraph Function | Evidence Anchor | Visual/Table | Maturity | Guardrail |
|---|---|---|---|---|---|
| METH-19 | Define the node integer-feasible set and prove canonical-route completeness through feasible depot-departure intervals under time-independent, nonnegative resources, nonnegative completion weights, no task-site or en-route waiting and supported depot-only waiting | EV002, EV009, EV031, EV033, EV035--EV037; manuscript (3), (24); CL039, CL041--CL042 | theorem block | IMPLEMENTED + NOW-PROOF | Environmental states are aggregated before optimization; unequal-travel-time paths cannot be removed; any reduced recharge time is absorbed as depot waiting; active-trip dominance is disabled and depot subset dominance uses the guards in Eq. (17) |
| METH-20 | Prove equivalence between feasible fleet schedules and the integer route master | EV002, EV003, EV009; manuscript (12), (24) | theorem block | NOW-PROOF | Exactness remains limited to the frozen logical-path solution space |
| METH-21 | Prove that exhaustive true-dual pricing converts an optimal RMP dual into a feasible full-master dual and hence closes the node LP | EV004, EV030; manuscript (13), (19), (25) | theorem block | NOW-PROOF | Unsupported dominance or completion pruning must be disabled; incomplete coverage cannot close a node |
| METH-22 | Prove SRI-3 integer validity and the disjoint, exhaustive same-route/different-route partition for every exact-valid Ryan–Foster pair | EV005, EV006, EV030; manuscript (20), (22), (26) | theorem block | NOW-PROOF | No fractional pair is not integrality; without a proved alternative branch the node remains incomplete |
| METH-23 | Prove that learning permutations and finite delays preserve the preceding lemmas once every deferred-pricing obligation is resolved | EV007, EV030; manuscript (23) | theorem block | NOW-PROOF + DESIGN | Learning may change the trace or valid branch pair, but not feasibility, bounds, cuts, pruning or proof records |
| METH-24 | Prove tree-level optimality by induction over exact node closure and state the fail-closed and numerical-tolerance qualifications | EV004–EV009, EV025, EV030–EV031; manuscript (27) | main theorem; FIG10 | NOW-PROOF | The theorem proves sound exact conclusions, not unconditional finite-time completion |
| METH-25 | Define audit fields required to activate the theorem in a run | EV007, EV025, EV030–EV031; EXP-L0/L1/L2 | audit table | DESIGN + NOW-PROOF | Any redline, open node, incomplete node or invalid ledger blocks a tree-level exact conclusion |

# 5. Experimental Design Blueprint

## Section purpose

Pre-register the comparison and exactness gates before results are inserted.
The section must make it impossible to fill a performance table without also
reporting equivalence, fallback and overhead.

| Unit | Paragraph Function | Evidence Anchor | Visual/Table | Maturity | Guardrail |
|---|---|---|---|---|---|
| EXP-1 | State research questions: exactness preservation, pricing-effort effect, incremental branch-ranking effect, held-out behavior and four-phase seasonal operating comparison | EV027; CL023–CL025, CL039 | experiment matrix | DESIGN | Phrase as questions, not expected outcomes; RQ5 remains unanswered until M006 |
| EXP-2 | Describe map sources, generator, 120 accepted instances, fleet sizes and 16–76 h scale-dependent horizons, then define 12 paired window-aggregated epoch families grouped into four south-polar phases | EV010, EV011, EV033; C063, C064; M006 | FIG01; TAB02–TAB03; epoch manifest and phase table | NOW-FROZEN + TBD-EVIDENCE | Use C063 for full-cycle structure and C064 for season-conditioned operational relevance; retain a southern-vernal-equinox reference, three anchors per phase and common controls; do not attribute the four groups or a phase effect to either source |
| EXP-3 | Define train/validation/test split by map/seed/scale and leakage controls | M001; EV027 | split table | TBD-RESULT | Must be supplied and frozen before training claims |
| EXP-4 | Define L0 no-learning, L1 pricing-guidance and L2 pricing-plus-branching variants | EXP-L0/L1/L2; EV001, EV007 | TAB08 shell | DESIGN | No learned-cut variant |
| EXP-5 | Define non-learning comparators, including deterministic scheduling/selective pricing where implementable | C059; exact framework | baseline table | DESIGN | Comparator configuration must be frozen |
| EXP-6 | Define training targets, loss, model selection, checkpoint/version and inference environment | M002–M003; EV027 | model table | TBD-RESULT | No hyperparameter fabrication |
| EXP-7 | Define exact-safety endpoints before performance metrics | EV004–EV007; M005 | audit table | DESIGN | Any safety failure blocks performance interpretation |
| EXP-8 | Define workload/performance metrics: time, labels, calls, iterations, nodes, proof time, overhead and fallback frequency | EV007; EXP-L0/L1/L2 | TAB08 shell | DESIGN | Report denominators and timeout/incomplete handling |
| EXP-9 | Define paired strict-cold protocol, repetition counts, intervals and multiple-seed handling | EV015–EV017 as design precedent | protocol table | DESIGN | Do not reuse deterministic SRI estimates as learning results |
| EXP-10 | Define held-out map/scale/OOD protocol and deterministic fallback | EXP-G; M005 | FIG16 shell | TBD-RESULT | No generalization claim without frozen split and results |
| EXP-11 | Define hardware, software, hashes, memory/time limits and artifact lineage | EV012, EV015, EV021 | reproducibility table | NOW-FROZEN + DESIGN | Each learning run must bind its own build/checkpoint |
| EXP-12 | Define the paired seasonal comparison using a southern-vernal-equinox reference, 12 anchors, four three-anchor phases, approximately 28.9-day spacing, scale-dependent mission windows, one-hour sampling, fixed aggregation, common inputs and common objective normalizers | C063, C064; EV033; CL039; M006 | epoch manifest, phase table and paired-result shell | TBD-RESULT | Cite the sources only for seasonal environmental and operational relevance; summarize anchors within paired families, use normalized science-weighted completion time as primary and reporting-only makespan as secondary, and exclude incomplete rows from ranking |

# 6. Computational Results Blueprint

## Evidence order

Correctness and evidence maturity precede performance. Existing deterministic
exact-framework evidence may be reported now; learning results remain explicit
slots.

| Unit | Paragraph/Result Function | Evidence Anchor | Visual/Table | Maturity | Guardrail |
|---|---|---|---|---|---|
| RES-1 | Validate frozen no-cut exact closure and artifact binding on 80 scale-5/10/20/30 cases | EV012, EV013; CL015 | TAB04 | NOW-FROZEN | Scope only to frozen build and 80 cases |
| RES-2 | Describe observed cold-start scaling with mean/p50/max, without causal overreach | EV014; CL016 | FIG12; TAB04 | NOW-FROZEN | Descriptive trend, not complexity theorem |
| RES-3 | Report formal deterministic P0 root-only SRI-3 experiment: correctness passed, overall promotion failed at scale 30 | EV015–EV017; CL017 | FIG13; TAB05 | NOW-BOUNDARY | State that the candidate was not promoted and that production continues to omit the optional cut family |
| RES-4 | Report exact state optimization and controlled replay as implementation/equivalence evidence | EV018, EV019; CL018 | TAB06 | NOW-BOUNDARY | Byte/replay facts are not general speedup |
| RES-5 | Move the one-pair diagnostic and 160-slot optimized benchmark to an explicitly exploratory appendix result | EV020–EV024; CL019–CL021 | FIG14; appendix table | NOW-BOUNDARY | Single-repeat benchmark-only; not formal promotion or learning |
| RES-6 | Report L0–L2 exactness-equivalence gates | EV027; EXP-L0/L1/L2 | safety table | TBD-RESULT | No performance paragraph if a gate fails |
| RES-7 | Report primary learned-pricing effect versus L0 | EV027; CL023 | FIG15; TAB08 | TBD-RESULT | Include inference overhead and exact fallback |
| RES-8 | Report incremental learned-branch effect L2 versus L1 | EV027; CL024 | FIG15; TAB08 | TBD-RESULT | Compare over the same valid candidate set |
| RES-9 | Report heterogeneous effects by scale/hardness and failure cases | EV027 | supplementary table | TBD-RESULT | Show degradations and incomplete rows, not only wins |
| RES-10 | Report held-out/OOD behavior and fallback/calibration | EV027; CL025 | FIG16 | TBD-RESULT | No transfer claim without frozen held-out design |
| RES-11 | Report paired four-phase changes in path space, feasibility, normalized science-weighted completion time, reporting-only makespan, resources and route structure | C063; EV033; CL039; M006; EXP-EPOCH | seasonal phase table | TBD-RESULT | Use family-level phase summaries, paired contrasts and uncertainty; separate infeasible and incomplete cases; do not claim a universal best season |
| RES-12 | Report scale-50/100 legal incompleteness as an exact-framework resource boundary | EV025; CL022 | TAB07 | NOW-BOUNDARY | No optimality or no-negative claim |

# 7. Discussion and Limitations Blueprint

| Unit | Paragraph Function | Evidence/Citation Anchor | Maturity | Guardrail |
|---|---|---|---|---|
| DISC-1 | Answer the research questions in evidence-strength order | RES-6–RES-11 | TBD-RESULT | Activate each answer only after its own learning or epoch evidence exists |
| DISC-2 | Explain why pricing is the primary learning target and branch ranking is secondary | EV001, EV004, EV005, EV007; C001, C002, C059 | DESIGN | Mechanistic rationale, not post-hoc superiority |
| DISC-3 | Interpret validated changes in fleet-planning reliability, computational accessibility or resource allocation | C022, C025, C039; future results | TBD-RESULT | No operational benefit without measured solver result |
| DISC-4 | Discuss exactness and proof transfer: what is invariant and what depends on the fixed solution space | EV004–EV009 | NOW-PROOF | Repeat conditions and fail-closed behavior |
| DISC-5 | State data/model limitations: map proxies, independently window-aggregated epochs, fixed paths, deterministic inputs, corpus scales and no continuous navigation guarantee | EV009–EV011, EV033; C052–C055, C063; CL039 | NOW-PROOF + CITATION | Distinguish 28.9-day anchor spacing, one-hour preprocessing and 16–76 h routing horizons; long cycles do not make polar shadow invariant; separate per-instance exactness from environmental fidelity |
| DISC-6 | State computational limitations: scale-50/100 memory boundary and incomplete learning evidence | EV025, EV027 | NOW-BOUNDARY | Incompleteness is not failure of exactness |
| DISC-7 | Define future work: rolling environmental updates or replanning built on frozen residual instances, richer path generation, uncertainty and validated learning transfer | C024, C039, C046, C063; EV027; CL039 | CITATION + DESIGN | Per-update exactness does not prove the global adaptive policy; genuine departure-time-dependent paths require a new pricing state and proof |

# 8. Conclusion Blueprint

| Unit | Paragraph Function | Evidence Anchor | Maturity | Guardrail |
|---|---|---|---|---|
| CONC-1 | Restate the transportation problem, formulation and learning/exact division | EV001–EV011 | DESIGN + NOW-PROOF | No new claim |
| CONC-2 | Summarize only evidence-backed exact and learning results | EV012–EV027 | MIXED | Learning sentence remains `TBD` until frozen |
| CONC-3 | Close with bounded planning significance and limitations | EV009–EV011, EV025 | NOW-BOUNDARY | No continuous-terrain, field-deployment or scientific-yield claim |

# Appendix Blueprint

| Appendix | Function | Evidence Anchor | Planned Visual/Table | Maturity |
|---|---|---|---|---|
| A | Full notation, resource transitions and exactness assumptions | EV002–EV009 | expanded TAB01 | NOW-PROOF |
| B | Root-only SRI-3 validity, Phase-I and reduced-cost audit details | EV006, EV015–EV019 | FIG13; TAB05–TAB06 | NOW-FROZEN/BOUNDARY |
| C | Benchmark-only optimized-candidate and one-pair diagnostic evidence | EV020–EV024 | FIG14 | NOW-BOUNDARY |
| D | Scale-50/100 fail-closed resource-limit records | EV025 | TAB07 | NOW-BOUNDARY |
| E | Learning dataset/checkpoint/run manifests and extended ablations | EV027 | extended TAB08; FIG15–FIG16 | TBD-RESULT |

## Figure and Table Placement Contract

| Asset | First Argument-Bearing Reference | Caption Claim Boundary |
|---|---|---|
| FIG01 | PROB-1 | Map/context provenance only; identify measured, derived and visualization layers |
| FIG06 | PROB-2 | Three predeclared path options; not continuous path optimization |
| FIG09 | METH-1 | Learning orders work; exact path owns proof |
| FIG10 | METH-1/METH-10 | Explicitly show no learned cut control and no learned proof path |
| FIG11 | METH-2 | Include fail-closed incomplete transition |
| FIG12 | RES-2 | Frozen no-cut descriptive scaling over 20 instances per scale |
| FIG13 | RES-3 or Appendix B | Formal deterministic P0 result must show failed scale-30 gate |
| FIG14 | Appendix C | Benchmark-only, single-repeat, not formally promoted |
| FIG15 | RES-7/RES-8 | `TBD` until L0/L1/L2 evidence is frozen |
| FIG16 | RES-10 | `TBD` until held-out/OOD evidence is frozen |
| TAB08 | EXP-4, then RES-6–RES-8 | Empty result cells remain `TBD`; no expected signs |

## Result-Insertion Contract

A `TBD-RESULT` unit may be activated only when all of the following are added to
the evidence bank:

1. frozen dataset and train/validation/test split manifest;
2. leakage audit and feature-schema version;
3. checkpoint hash and inference configuration;
4. exact solver/config/native-engine hashes;
5. paired run rows and summary with repetition design;
6. objective/proof/reduced-cost equivalence audit;
7. permanent-drop, unresolved deferred-pricing, fallback and unsupported-proof checks;
8. measured workload and inference-overhead fields;
9. held-out/OOD definition when a transfer claim is proposed.

## Claim Coverage Check

| Claim Group | Blueprint Units |
|---|---|
| CL001–CL005: application, formulation and scope | INT-1–INT-3; PROB-1–PROB-10 |
| CL006–CL011: exact BPC and guidance contract | METH-1–METH-21 |
| CL012–CL014: implementation/data status | METH-13–METH-14; EXP-2 |
| CL015–CL022: available computational evidence | RES-1–RES-5; RES-11; Appendices B–D |
| CL023–CL025: missing learning results | EXP-1–EXP-11; RES-6–RES-10 |
| CL026–CL029: forbidden claims | Title constraints; INT-6; RW-9–RW-10; all guardrail columns |
| CL030: citation-required context | INT-1–INT-5; RW-1–RW-10 |
# 2026-08-03 P0V4+V5/QG2 replacement blueprint

This update supersedes older paragraph plans wherever they describe a generic pricing-plus-branch GAT as the current implementation.

| Section | Revised paragraph function | Evidence allocation | Claim boundary |
|---|---|---|---|
| Abstract | Define lunar model; state P0V4+V5 exact pipeline; state QG2 ordering-only candidate; report 80/80 at 5–30 and 15/20 at 50; withhold GAT performance | EV038–EV042 | No GAT acceleration claim |
| 1 | Funnel from in-situ lunar evidence need to multi-path multi-trip routing, exact-search burden, then current exact and learning contributions | EV032–EV042; locked citations | Three contributions only: model, exact algorithm/learning interface, benchmark/evaluation |
| 3 | Preserve no-task-wait formulation, fixed mission-epoch inputs, normalized objective, full classical feasibility conditions and route master | EV029, EV031–EV035 | No departure-time-dependent path attributes inside a solve |
| 4.1 | Present deterministic P0V4+V5 flow before learning | EV038 | Midpoint and cut screens are accelerators, not proofs |
| 4.3 | Add bidirectional midpoint witness stage, true-RC audit, diverse batch admission and exhaustive P0V4 fallback | EV038 | Only fallback exhaustion proves no negative column |
| 4.4 | Replace old top-cut-only rule with deterministic group screen over root-only SRI-3 candidates | EV038 | Screening changes cut commitment only; cut validity remains mathematical |
| 4.5 | Retain exact Ryan–Foster branch rule | EV030, EV038 | No current learned branch result |
| 4.6 | Replace generic GAT with QG2 label-state ordering: action surface, features, supervision, fail-closed activation | EV041–EV042 | Design/implementation status only |
| 4.7 | Extend invariance lemma to midpoint, group screen and within-bucket QG2 permutations | EV031, EV038, EV041 | Conditional exactness, not guaranteed finite-time closure |
| 5 | Define paired P0V4/Q0/QG2 experiment; separate Oracle, calibration, E2E and formal gates | EV039–EV042 | All QG2 outcome fields remain TBD |
| 6.1 | Report current exact baseline | EV039–EV040 | 50-task incomplete cases shown explicitly |
| 6.2 | Report V5 component status without unrun causal ablation | EV038 | No component speedup unless paired ablation is frozen |
| 6.3 | Record rejected earlier GAT paths only as design evidence; do not use them as proposed-result support | GAT closeout plus EV042 | Negative/unfinished evidence kept distinct |
| 6.4 | State QG2 preparation status and activation criteria | EV041–EV042 | No learned result |
| 7–8 | Discuss exactness scope, computational frontier and pending learning/seasonal evidence | EV039–EV042 | No continuous-terrain or seasonal optimum claim |

# 2026-08-03 Chinese narrative-rewrite contract

This contract supersedes implementation-status wording in the visible Chinese manuscript while preserving the mathematical and evidence boundaries above.

| Section | Reader question | Narrative move | Evidence retained | Material moved out of the visible argument |
|---|---|---|---|---|
| Abstract | What lunar planning problem is solved, by what exact mechanism, and what is already known? | Problem and lunar resource coupling → route-column model → exact/learning division → bounded deterministic evidence | Equation (11) objective identity; EV039–EV042 | Internal version names, model qualification status and development history |
| 1 | Why does remote water evidence lead to a fleet-routing problem? | Remote anomaly → in-situ evidence → south-pole path trade-offs → multi-path multi-trip structure → pricing bottleneck → proof-preserving learning | C042, C054, C055, C061, C062; EV032–EV042 | Failed learning branches and implementation acceptance language |
| 2 | Which research lines are combined, and what remains unresolved? | Lunar local/task planning → route-column exact VRP → learning-guided search; each subsection ends at the paper-specific gap | C001–C003, C009, C020–C030, C041–C055 | Proof-ledger vocabulary and generic citation listing |
| 3 | What is feasible, and how is a complete mission represented? | Task network → no-wait trip timing → route topology/time/resources → multi-trip route → set-partitioning master | EV029, EV031–EV035 | Code validation-model terminology and uncalibrated physical mixing coefficients |
| 4 | How does the solver progress from finding columns to proving a node? | RMP → fast negative-column witnesses → exhaustive SPPRC → root valid cuts → deterministic branch → local GAT order → whole-tree proof | EV038, EV041–EV042; exactness lemmas | Raw implementation IDs, hash/checklist prose and learned-cut or learned-branch implications |
| 5 | How will each contribution be tested fairly? | Questions → official lunar data and instance construction → paired deterministic and learning comparisons → implementation → metrics | EV010–EV011, EV033, EV039–EV042; C063–C064 | Gate/oracle/deployment vocabulary and historical version comparisons |
| 6 | What is supported now, and what still requires experiments? | Report exact scalability first; state missing causal, learning and epoch evidence without assigning effects | EV039–EV040 | Failed-model development chronicle and visible project-management instructions |
| 7–8 | What do the formulation and current evidence mean for lunar planning? | Lunar decision interpretation → exactness and resource boundary → model limits and extensions → concise conclusion | EV009–EV011, EV025, EV039–EV042 | Repetition of implementation checks and speculative operational claims |
