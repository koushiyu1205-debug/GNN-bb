# Section Blueprints

## Blueprint Status

- Workflow: `build_from_materials`
- Scene: journal article
- Target: *Transportation Research Part C: Emerging Technologies*
- Output language: English
- Controlling motivation: pricing-led, branching-assisted learning guidance
  inside an exact Branch-Price-and-Cut framework for lunar water-ice
  exploration fleet routing.
- Drafting permission: Phase 3 authorized on 2026-07-23. Section 3 has entered
  the first drafting pass; remaining sections retain their blueprint status
  until drafted.
- Evidence snapshot: 2026-07-23 (Asia/Shanghai)

## Working Title and Throughline

### Preferred working title

**Proof-Preserving Learning Guidance for Exact Branch-Price-and-Cut in
Lunar Water-Ice Exploration Fleet Routing**

### Alternate title

**Pricing-Led Learning Guidance in Exact Branch-Price-and-Cut for
Resource-Constrained Lunar Exploration Routing**

### Title constraints

- Show both the transportation problem and the solution class.
- Do not include a speedup, solved scale, “first,” “novel,” or trained-GAT
  claim.
- Keep “proof-preserving” only if the final method and experiments retain
  the exact fallback and audit evidence specified below.

### Whole-paper claim

The paper formulates a fixed logical-path solution space, resource-constrained, multi-sortie lunar
fleet-routing problem and develops an exact BPC architecture in which learned
policies prioritize pricing effort and rank valid branch candidates, while
exact pricing completion, deterministic cut logic, branch
validity/completeness, bounds, pruning and proofs remain exclusively on
the exact path.

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
| Model | What exactly is optimized and where does exactness apply? | Multi-sortie journey columns over a fixed logical graph with three path options per directed edge | EV002, EV003, EV009, EV010 |
| Method | What does learning control, and what remains exact? | Learning orders pricing work and valid branch candidates; deterministic exact logic owns cuts, completeness, proof and proofs | EV001, EV004–EV008 |
| Evidence | What must be tested before the method can claim value? | Exact equivalence first, then pricing ablation, incremental branch ablation, overhead/fallback and held-out behavior | EV027; EXP-L0/L1/L2/G |
| Interpretation | What does the evidence mean for fleet planning, and what does it not mean? | Translate validated solver behavior into planning reliability while preserving map, fixed logical-path solution-space, scale and data limits | EV009–EV011, EV025; C039, C052–C055 |

## Planned Core Citation Set

The following 20 candidates form the initial citation budget. Bibliographic and
passage verification remains mandatory before insertion.

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
| ABS-2 | State the fixed logical-path solution space multi-sortie formulation and exact BPC framework | EV002–EV006, EV009 | NOW-PROOF | Include fixed logical-path solution space scope |
| ABS-3 | State the pricing-led and branching-assisted learned actions | EV001, EV007, EV008 | DESIGN | Learning ranks work/candidates; it does not prove or control cuts |
| ABS-4 | State the exactness contract | EV004, EV005, EV007 | NOW-PROOF | Exact completion and fallbacks remain mandatory |
| ABS-5 | Reserve the numerical result sentence | EV027; EXP-L0/L1/L2/G | TBD-RESULT | No result wording until frozen learning evidence exists |
| ABS-6 | State a bounded implication and limitation | EV009–EV011 | DESIGN | No continuous-terrain or scientific-yield claim |
| KEYWORDS | Use 5–7 searchable terms | lunar exploration routing; multi-sortie fleet routing; branch-price-and-cut; resource-constrained shortest path; learning-guided optimization; exact algorithms | DESIGN | Avoid “learning to cut” |

# 1. Introduction Blueprint

## Section purpose

Move from a transportation-system consequence to one precise algorithmic gap.
The section must make the learning/exact split inevitable before presenting the
contribution list.

| Unit | Paragraph Function | Evidence/Citation Anchor | Visual | Maturity | Guardrail |
|---|---|---|---|---|---|
| INT-1 | Establish water-ice prospecting as a mission-level movement and site-sequencing problem under terrain, illumination, energy, thermal and communication constraints | C041, C042, C054, C055 | none | CITATION | Application need only; no project performance |
| INT-2 | Reframe autonomous rovers as a resource-constrained transportation fleet whose assignments, journeys and replenishment decisions are coupled | C022, C025; EV001 | none | CITATION + DESIGN | Do not reduce the problem to local collision avoidance |
| INT-3 | Explain why local trajectory/waypoint planning and mission-level exact fleet routing are complementary but different scopes | C041, C044, reserve C045; EV009 | none | CITATION | Do not claim heuristic lunar planners are inferior |
| INT-4 | Introduce exact route-based decomposition and the computational burden of resource-rich pricing and branch-tree closure | C020, C021, C028, C029, C030, C060; EV002–EV006 | none | CITATION + NOW-PROOF | Do not claim asymptotic cause from observed scaling |
| INT-5 | Review the opportunity and risk of learning-guided pricing/branching: lower effort is a hypothesis, while proof ownership must remain exact | C001, C002, C003, C008, C009, C059 | none | CITATION | A score is not a no-negative or branch-completeness proof |
| INT-6 | State the specific gap: proof-preserving integration of pricing-led learning and limited branch ranking for lunar multi-sortie BPC, with no learned cut control | EV001, EV007; C001, C002, C020 | none | DESIGN | No “first” claim |
| INT-7 | Give a three-part contribution list: formulation, exact-safe guidance architecture, and evidence protocol/validation | CL001–CL011; EV027 | none | MIXED | Separate implemented exact framework from proposed/unvalidated learning effects |
| INT-8 | Preview the evidence order and paper organization | EV012–EV027 | none | DESIGN | Existing SRI evidence is framework evidence, not learning evidence |

## Introduction exit condition

The reader should be able to state: (i) the transportation decision, (ii) the
fixed logical-path solution space exactness scope, (iii) why pricing is the primary learned target,
(iv) why branch ranking is secondary, and (v) why cuts and proofs remain
deterministic.

# 2. Related Work Blueprint

## 2.1 Lunar surface planning and autonomous exploration

| Unit | Paragraph Function | Citation Anchor | Maturity | Guardrail |
|---|---|---|---|---|
| RW-1 | Organize lunar work by local navigation, mission-level safe traversal, path-network construction and multi-robot coordination | C041–C049 | CITATION | Taxonomy only; verify each scope |
| RW-2 | Identify the unfilled formulation space: exact multi-sortie fleet assignment and journey selection over predeclared path alternatives | C041, C044, C049; EV009, EV010 | CITATION + NOW-PROOF | Present as a scoped contrast, not universal absence |
| RW-3 | Connect terrain/illumination/map provenance to optimization inputs and later limitations | C044, C052, C053, C055; EV011 | CITATION | Derived resource/risk maps are not direct ice ground truth |

## 2.2 Exact route-based optimization and BPC

| Unit | Paragraph Function | Citation Anchor | Maturity | Guardrail |
|---|---|---|---|---|
| RW-4 | Explain how structured route/journey columns encode internal resource processes | C021, C029, C030 | CITATION | Use precedents for structure, not project validation |
| RW-5 | Position tailored SPPRC pricing, valid inequalities and branching as standard proof-bearing BPC components | C020, C023, C028, C060 | CITATION | Do not claim BPC/SRI as novel by themselves |
| RW-6 | Distinguish selective/stabilized pricing schedules from exact pricing termination | C059 and reserve C027 | CITATION | Pricing control is a baseline; exact completion remains separate |

## 2.3 Learning to guide exact optimization

| Unit | Paragraph Function | Citation Anchor | Maturity | Guardrail |
|---|---|---|---|---|
| RW-7 | Summarize foundational and recent learning-to-branch work, ending with exact vehicle-routing BPC precedent | C056, C057, C003, C001 | CITATION | C001 blocks any “first learning-guided exact BPC” claim |
| RW-8 | Summarize learned pricing/column-generation control and identify exact fallback as the unresolved proof production requirement for this paper | C002, C009, C059 | CITATION | Learned column discovery cannot prove exhaustion |
| RW-9 | Delimit the excluded learned-cut direction | C004, C006, C007 or C058; EV001, EV006, EV007 | CITATION + NOW-PROOF | One concise boundary paragraph; do not create a learned-cut contribution |
| RW-10 | Close with the paper-specific integration gap and evaluation burden | SOTA gap map; EV001, EV027 | DESIGN | Gap is application/interface/validation-specific, not a universal novelty claim |

# 3. Problem Setting and Mathematical Formulation Blueprint

## 3.1 Transportation network, map inputs and fixed path-option space

| Unit | Paragraph/Model Function | Evidence Anchor | Visual/Table | Maturity | Guardrail |
|---|---|---|---|---|---|
| PROB-1 | Define depot, task sites, rover fleet, operation modes and directed logical graph | EV010, EV011 | FIG01; TAB02–TAB03 | NOW-PROOF | Distinguish data inputs from mission observations |
| PROB-2 | Define three declared path options per directed edge and path attributes | EV009, EV010 | FIG06 | NOW-PROOF | State that runtime does not optimize over continuous paths |
| PROB-3 | State exactness scope and modeling assumptions | EV009; CL005 | TAB01 | NOW-PROOF | Repeat fixed logical-path solution space qualifier before any optimality language |

## 3.2 Tasks, sorties and multi-sortie journeys

| Unit | Paragraph/Model Function | Evidence Anchor | Visual/Table | Maturity | Guardrail |
|---|---|---|---|---|---|
| PROB-4 | Define task requirements, service modes, time windows, science weights and resource attributes | EV010; source S006 | TAB01 | NOW-PROOF | Do not invent parameter values not in manifests/config |
| PROB-5 | Define sortie feasibility: depot return, time, energy, shadow exposure, ice load and task compatibility | EV002; source S006 | TAB01 | NOW-PROOF | Keep every resource transition consistent with pricing |
| PROB-6 | Define a journey as one rover's ordered collection of compatible sorties with recharge/docking relations | EV002; CL003 | FIG09 | NOW-PROOF | A journey is not a single route/sortie |

## 3.3 Objective and journey master

| Unit | Paragraph/Model Function | Evidence Anchor | Visual/Table | Maturity | Guardrail |
|---|---|---|---|---|---|
| PROB-7 | Define the normalized additive objective and its operating-cost, risk and weighted-completion terms | EV002, EV003; CL002 | TAB01 | NOW-PROOF | Current completion weight 0.4 only where configuration is stated |
| PROB-8 | State that makespan is a reporting metric, not a pricing/master objective term | EV003 | TAB01 note | NOW-PROOF | Never add makespan without a linking variable |
| PROB-9 | Present binary journey variables, exact task-cover constraints and fleet-size constraint | EV002; CL003 | TAB01 | NOW-PROOF | Preserve set-partitioning equality |
| PROB-10 | Derive the journey reduced cost with task, fleet and active deterministic-cut duals | EV002, EV006; CL004 | equation block | NOW-PROOF | Branch restrictions are feasibility context, not duals |

# 4. Pricing-Led, Branching-Assisted Exact BPC Blueprint

## 4.1 Architecture and responsibility boundary

| Unit | Paragraph Function | Evidence Anchor | Visual | Maturity | Guardrail |
|---|---|---|---|---|---|
| METH-1 | Introduce the full node loop and the two-lane heuristic/exact responsibility split | EV001, EV004–EV008 | FIG09–FIG10 | DESIGN + NOW-PROOF | No learning arrow into cut control, bounds, pruning or proofs |
| METH-2 | Define algorithm statuses and fail-closed transitions | EV004, EV025; source S022 | FIG11 | NOW-PROOF | `INCOMPLETE_LIMIT` cannot become proved no-negative |

## 4.2 Restricted master and column lifecycle

| Unit | Paragraph Function | Evidence Anchor | Visual | Maturity | Guardrail |
|---|---|---|---|---|---|
| METH-3 | Explain initial columns, RMP solution, true-dual extraction and column admission | EV002, EV004; S016 | FIG11 | NOW-PROOF | Use the same reduced-cost definition throughout |
| METH-4 | Explain addability, duplicate handling, pool updates and audit bindings | EV004, EV006; S016–S018 | FIG11 | NOW-PROOF | Heuristic priority never changes column validity |

## 4.3 Native exact SPPRC pricing

| Unit | Paragraph Function | Evidence Anchor | Visual/Table | Maturity | Guardrail |
|---|---|---|---|---|---|
| METH-5 | Define label resources and transitions for task visits, paths, time, energy, load, shadow and risk | EV002, EV004; S017–S019 | state table | NOW-PROOF | Include only implemented resources |
| METH-6 | Explain dominance, branch/cut feasibility context and exact terminal acceptance | EV004–EV006; S019–S020 | FIG11 | NOW-PROOF | Any unsupported context must fail closed |
| METH-7 | Separate fast/ordered pricing work from mandatory true-dual exact completion | EV004, EV007; C059 | FIG10–FIG11 | NOW-PROOF | Only completion may prove no negative column |

## 4.4 Deterministic cut strengthening

| Unit | Paragraph Function | Evidence Anchor | Visual/Table | Maturity | Guardrail |
|---|---|---|---|---|---|
| METH-8 | Define deterministic SRI-3/SRI-5 validity and coefficient handling | EV006; S021 | optional appendix algorithm | NOW-PROOF | Do not present live SRI as the learning contribution |
| METH-9 | Explain active-cut Phase-I, reduced-cost reconstruction, lineage and proof binding | EV006 | FIG11 | NOW-PROOF | Cut context must be visible to exact pricing |
| METH-10 | State the learning exclusion: no learned generation, selection, activation, retention or removal | EV001, EV006, EV007; CL009, CL027 | FIG10 | NOW-PROOF | No learned-cut ablation |

## 4.5 Exact branching and completeness

| Unit | Paragraph Function | Evidence Anchor | Visual | Maturity | Guardrail |
|---|---|---|---|---|---|
| METH-11 | Define Ryan–Foster same/different-journey candidate construction and child feasibility | EV005; S020 | FIG11 | NOW-PROOF | “Journey,” not “sortie” |
| METH-12 | Define fallback when no fractional Ryan–Foster pair exists | EV005; CL008 | FIG10–FIG11 | NOW-PROOF | `NO_FRACTIONAL_RF_PAIR` is not integrality |

## 4.6 Graph state and learning outputs

| Unit | Paragraph Function | Evidence Anchor | Visual/Table | Maturity | Guardrail |
|---|---|---|---|---|---|
| METH-13 | Specify the planned graph representation: task/path/resource features plus solver context | EV007, EV008; C003, C008 | feature table | DESIGN | Architecture/hyperparameters remain `TBD` until model artifacts exist |
| METH-14 | Define typed output heads and context/version/OOD metadata | EV007, EV008; S023–S024 | interface table | DESIGN | Current `no_model_shadow_v1` is a scaffold, not a trained model |

## 4.7 Primary learned pricing guidance

| Unit | Paragraph Function | Evidence Anchor | Visual | Maturity | Guardrail |
|---|---|---|---|---|---|
| METH-15 | Define which pricing work items may be ranked and the objective of prioritization | EV001, EV007; C002, C009, C059 | FIG09–FIG10 | DESIGN | Do not claim reduced effort before EXP-L1 |
| METH-16 | Define finite delay, proof-debt accounting and mandatory release/repricing before proof production | EV007 | FIG10–FIG11 | NOW-PROOF + DESIGN | No permanent drop of a true-negative column |

## 4.8 Secondary learned branch-candidate ranking

| Unit | Paragraph Function | Evidence Anchor | Visual | Maturity | Guardrail |
|---|---|---|---|---|---|
| METH-17 | Define ranking over an exact-valid candidate set and expensive-evaluation ordering | EV001, EV005, EV007; C001, C003 | FIG09–FIG10 | DESIGN | Learning cannot invent validity or remove fallback |
| METH-18 | Define failure/OOD behavior and deterministic candidate selection fallback | EV005, EV007 | FIG10–FIG11 | DESIGN | No branch-performance claim before EXP-L2 |

## 4.9 Exactness proposition and audit contract

| Unit | Paragraph Function | Evidence Anchor | Visual/Table | Maturity | Guardrail |
|---|---|---|---|---|---|
| METH-19 | State assumptions under which reordering preserves the feasible solution space and objective | EV004, EV005, EV007, EV009 | proposition box | NOW-PROOF | The guarantee is conditional on complete exact fallback |
| METH-20 | Explain that official bounds, pruning, infeasibility and optimality proofs use only exact-path records | EV004–EV007; CL007, CL011 | FIG10 | NOW-PROOF | Diagnostics/confidence cannot enter proof fields |
| METH-21 | Define do-no-harm audit fields: objective/proof equivalence, RC audit, proof-debt clearance, candidate-set preservation and false-proof count | EV007; EXP-L0/L1/L2 | audit table | DESIGN | This is an acceptance protocol until frozen learning runs exist |

# 5. Experimental Design Blueprint

## Section purpose

Pre-register the comparison and exactness gates before results are inserted.
The section must make it impossible to fill a performance table without also
reporting equivalence, fallback and overhead.

| Unit | Paragraph Function | Evidence Anchor | Visual/Table | Maturity | Guardrail |
|---|---|---|---|---|---|
| EXP-1 | State research questions: exactness preservation, pricing-effort effect, incremental branch-ranking effect and held-out behavior | EV027; CL023–CL025 | experiment matrix | DESIGN | Phrase as questions, not expected outcomes |
| EXP-2 | Describe map sources, generator, 120 accepted instances and scale partition | EV010, EV011 | FIG01; TAB02–TAB03 | NOW-FROZEN | Do not claim all 120 are exactly solved |
| EXP-3 | Define train/validation/test split by map/seed/scale and leakage controls | M001; EV027 | split table | TBD-RESULT | Must be supplied and frozen before training claims |
| EXP-4 | Define L0 no-learning, L1 pricing-guidance and L2 pricing-plus-branching variants | EXP-L0/L1/L2; EV001, EV007 | TAB08 shell | DESIGN | No learned-cut variant |
| EXP-5 | Define non-learning comparators, including deterministic scheduling/selective pricing where implementable | C059; exact framework | baseline table | DESIGN | Comparator configuration must be frozen |
| EXP-6 | Define training targets, loss, model selection, checkpoint/version and inference environment | M002–M003; EV027 | model table | TBD-RESULT | No hyperparameter fabrication |
| EXP-7 | Define exact-safety endpoints before performance metrics | EV004–EV007; M005 | audit table | DESIGN | Any safety failure blocks performance interpretation |
| EXP-8 | Define workload/performance metrics: time, labels, calls, iterations, nodes, proof time, overhead and fallback frequency | EV007; EXP-L0/L1/L2 | TAB08 shell | DESIGN | Report denominators and timeout/incomplete handling |
| EXP-9 | Define paired strict-cold protocol, repetition counts, intervals and multiple-seed handling | EV015–EV017 as design precedent | protocol table | DESIGN | Do not reuse deterministic SRI estimates as learning results |
| EXP-10 | Define held-out map/scale/OOD protocol and deterministic fallback | EXP-G; M005 | FIG16 shell | TBD-RESULT | No generalization claim without frozen split and results |
| EXP-11 | Define hardware, software, hashes, memory/time limits and artifact lineage | EV012, EV015, EV021 | reproducibility table | NOW-FROZEN + DESIGN | Each learning run must bind its own build/checkpoint |

# 6. Computational Results Blueprint

## Evidence order

Correctness and evidence maturity precede performance. Existing deterministic
exact-framework evidence may be reported now; learning results remain explicit
slots.

| Unit | Paragraph/Result Function | Evidence Anchor | Visual/Table | Maturity | Guardrail |
|---|---|---|---|---|---|
| RES-1 | Validate frozen no-cut exact closure and artifact binding on 80 scale-5/10/20/30 cases | EV012, EV013; CL015 | TAB04 | NOW-FROZEN | Scope only to frozen build and 80 cases |
| RES-2 | Describe observed cold-start scaling with mean/p50/max, without causal overreach | EV014; CL016 | FIG12; TAB04 | NOW-FROZEN | Descriptive trend, not complexity theorem |
| RES-3 | Report formal deterministic P0 SRI experiment: correctness passed, overall promotion failed at scale 30 | EV015–EV017; CL017 | FIG13; TAB05 | NOW-BOUNDARY | Keep `NOT_PROMOTED` and production `no_cut` visible |
| RES-4 | Report exact state optimization and controlled replay as implementation/equivalence evidence | EV018, EV019; CL018 | TAB06 | NOW-BOUNDARY | Byte/replay facts are not general speedup |
| RES-5 | Move the one-pair diagnostic and 160-slot optimized benchmark to an explicitly exploratory appendix result | EV020–EV024; CL019–CL021 | FIG14; appendix table | NOW-BOUNDARY | Single-repeat benchmark-only; not formal promotion or learning |
| RES-6 | Report L0–L2 exactness-equivalence gates | EV027; EXP-L0/L1/L2 | safety table | TBD-RESULT | No performance paragraph if a gate fails |
| RES-7 | Report primary learned-pricing effect versus L0 | EV027; CL023 | FIG15; TAB08 | TBD-RESULT | Include inference overhead and exact fallback |
| RES-8 | Report incremental learned-branch effect L2 versus L1 | EV027; CL024 | FIG15; TAB08 | TBD-RESULT | Compare over the same valid candidate set |
| RES-9 | Report heterogeneous effects by scale/hardness and failure cases | EV027 | supplementary table | TBD-RESULT | Show degradations and incomplete rows, not only wins |
| RES-10 | Report held-out/OOD behavior and fallback/calibration | EV027; CL025 | FIG16 | TBD-RESULT | No transfer claim without frozen held-out design |
| RES-11 | Report scale-50/100 legal incompleteness as an exact-framework resource boundary | EV025; CL022 | TAB07 | NOW-BOUNDARY | No optimality or no-negative claim |

# 7. Discussion and Limitations Blueprint

| Unit | Paragraph Function | Evidence/Citation Anchor | Maturity | Guardrail |
|---|---|---|---|---|
| DISC-1 | Answer the research questions in evidence-strength order | RES-6–RES-10 | TBD-RESULT | Write only after learning results exist |
| DISC-2 | Explain why pricing is the primary learning target and branch ranking is secondary | EV001, EV004, EV005, EV007; C001, C002, C059 | DESIGN | Mechanistic rationale, not post-hoc superiority |
| DISC-3 | Interpret validated changes in fleet-planning reliability, computational accessibility or resource allocation | C022, C025, C039; future results | TBD-RESULT | No operational benefit without measured solver result |
| DISC-4 | Discuss exactness and proof transfer: what is invariant and what depends on the fixed solution space | EV004–EV009 | NOW-PROOF | Repeat conditions and fail-closed behavior |
| DISC-5 | State data/model limitations: map proxies, fixed paths, deterministic inputs, corpus scales and no continuous navigation guarantee | EV009–EV011; C052–C055 | NOW-PROOF + CITATION | No ground-truth ice-yield inference |
| DISC-6 | State computational limitations: scale-50/100 memory boundary and incomplete learning evidence | EV025, EV027 | NOW-BOUNDARY | Incompleteness is not failure of exactness |
| DISC-7 | Define future work: richer path generation, uncertainty/online planning and validated learning transfer | C024, C039, C046; EV027 | CITATION + DESIGN | Keep outside current contribution |

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
| B | Deterministic SRI validity, Phase-I and reduced-cost audit details | EV006, EV015–EV019 | FIG13; TAB05–TAB06 | NOW-FROZEN/BOUNDARY |
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
7. permanent-drop, proof-debt, fallback and false-proof counters;
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
