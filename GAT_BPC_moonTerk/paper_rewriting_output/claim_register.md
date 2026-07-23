# Claim Register

## Status Vocabulary

| Status | Meaning |
|---|---|
| VERIFIED | Directly supported by a proof contract, implementation, provenance artifact, or frozen experiment |
| BOUNDED | Supported only within an explicit path-option space, scale, instance, resource, or experiment design |
| DIAGNOSTIC_ONLY | May be reported only as a diagnostic observation |
| DESIGN_ONLY | Confirmed proposed method or implemented scaffold without effectiveness evidence |
| CITATION_REQUIRED | Contextual or comparative claim requiring an external citation |
| TBD | Evidence is planned but absent |
| FORBIDDEN | Available evidence contradicts the claim or cannot support it |

## Registered Claims

| Claim ID | Proposed Claim | Evidence IDs | Strength | Status | Allowed Wording | Avoid | Expected Draft Location |
|---|---|---|---|---|---|---|---|
| CL001 | The application is multi-sortie fleet routing for lunar water-ice prospecting under terrain, risk, energy, time-window, capacity and shadow constraints, with exact solution claims requiring explicit proofs | EV001, EV010, EV011 | Moderate | VERIFIED | “This paper considers…” followed by the actual model and proof scope | Operational mission validation or physical realism beyond the recorded inputs | Introduction; problem description |
| CL002 | The mathematical objective is normalized additive operating cost, risk and weighted completion, with configured completion weight 0.4; makespan is a reporting metric | EV002, EV003 | Strong | VERIFIED | State the implemented objective exactly | Add makespan to the objective or use an incompatible raw objective | Problem formulation |
| CL003 | The master selects multi-sortie journey columns subject to exact task coverage and a fleet-size constraint | EV002 | Strong | VERIFIED | Present the RMP equations and integer restriction | Describe columns as single sorties or ordinary VRP routes | Problem formulation |
| CL004 | Journey reduced cost includes task-cover, fleet-limit and active deterministic-cut dual terms under a single audited definition | EV002, EV006 | Strong | VERIFIED | Present one reduced-cost expression shared by pricing/audit/proof | Treat branch restrictions as dual terms | Method |
| CL005 | Exactness is defined over the fixed logical graph and three path options per directed edge | EV009, EV010 | Strong | BOUNDED | “Exact within the frozen fixed logical-path solution space” | “Globally optimal lunar-surface trajectory” | Problem scope; limitations |
| CL006 | The exact solver uses a restricted master, native exact SPPRC pricing and branch-and-price closure with deterministic cut support | EV004–EV006, EV012 | Strong | VERIFIED | Describe the implemented exact architecture and current opt-in cut boundary | Attribute proof to heuristics or learning | Method |
| CL007 | A true-dual native exact completion pass is the sole source of a no-negative-column proof | EV004 | Strong | VERIFIED | Use “sole proof-bearing completion path” | Say heuristic/learned pricing proves closure | Exactness analysis |
| CL008 | Ryan–Foster same/different-journey branching is used, and no-fractional-pair cases require exact fallback or an aggregation proof | EV005 | Strong | VERIFIED | State validity and completeness separately | Treat the candidate rule as an integrality proof | Method; exactness analysis |
| CL009 | Deterministic SRI logic may strengthen BPC, but learning does not generate or manage cuts | EV001, EV006, EV007 | Strong | VERIFIED | “Cuts remain deterministic and auditable” | “Learning-guided cuts,” “learned cut selection,” or equivalent | Contribution list; method |
| CL010 | The proposed learning layer primarily ranks pricing work and secondarily ranks an already valid branch-candidate set | EV001, EV007 | Strong as scope | DESIGN_ONLY | “The proposed guidance layer is designed to…” | Present-tense effectiveness or trained-model claims | Contributions; proposed guidance |
| CL011 | Guidance cannot create bounds, prune nodes, validate branches, permanently drop required negative columns or construct proofs | EV007 | Strong | VERIFIED | State as an exact-safe interface contract | Imply that confidence or ranking scores are proof evidence | Exactness analysis |
| CL012 | The current repository contains guidance interfaces and shadow/ordering scaffolding, not a trained GAT result | EV008 | Strong | VERIFIED | State this in development/evidence limitations if needed | Claim an implemented trained model or learned acceleration | Experimental setup/limitations |
| CL013 | The benchmark corpus has 120 accepted instances across scales 5, 10, 20, 30, 50 and 100 with recorded generation policies | EV010 | Strong | VERIFIED | Report manifest-backed counts and policies | Say 120 instances were all solved exactly | Data section |
| CL014 | The map-source catalog records the locally available LOLA layers and the role/native resolution of optional inputs | EV011 | Strong | VERIFIED | Distinguish present, optional and absent layers | Say absent M3/LEND/Diviner data were used | Data section |
| CL015 | The frozen no-cut baseline solved all 80 cases at scales 5–30 exactly with objective closure and no-cheat gates | EV012, EV013 | Strong | VERIFIED | Report 80/80 and 20 cases per scale under the frozen design | Extend the result to scales 50/100 or another build | Experiments |
| CL016 | Frozen no-cut runtime increases sharply with scale under the current corpus and implementation | EV014 | Moderate | BOUNDED | Report scale-wise mean/p50 and describe the observed trend | Claim a universal complexity law or causal source without analysis | Experiments; motivation |
| CL017 | The formal 1040-slot P0 live-SRI experiment passed correctness but was not promoted because scale 30 failed its performance gate | EV015, EV016, EV017 | Strong | VERIFIED | Report the complete negative promotion result | Say live SRI is the production default or uniformly faster | Experiments; discussion |
| CL018 | Exact nonzero-dual projection and packed exact-overlap state reduce stored state while preserving the audited full proof context | EV018, EV019 | Strong for implementation | VERIFIED | Report byte counts and replay-equivalence scope | Claim general end-to-end acceleration or memory scaling | Implementation details; ablation |
| CL019 | One scale-20 instance showed a lower optimized-P0 time in a single strict-cold diagnostic pair | EV020 | Weak | DIAGNOSTIC_ONLY | Include “one instance,” “one run per mode,” and “not promotion evidence” | General speedup, significance, or learning effect | Appendix or diagnostic note |
| CL020 | The later optimized candidate completed a 160-slot single-repeat paired benchmark with favorable scale-20/30 geometric-mean ratios | EV021–EV023 | Moderate | BOUNDED | Include “benchmark-only,” “single repeat,” candidate identity and intervals | Formal promotion, repeated-run stability or production approval | Exploratory results/appendix |
| CL021 | The 160-slot optimized-candidate benchmark does not authorize a default switch | EV024 | Strong | VERIFIED | Explicitly state all three false fields | Infer promotion from scale-local gates | Results boundary; discussion |
| CL022 | The scale-50 and scale-100 bounded tests failed closed at the memory limit without leaking an exact proof | EV025 | Strong | BOUNDED | “Legal incomplete under an approximately 8 GiB effective limit” | “Solved,” “proved infeasible,” or “proved no negative column” | Scalability limitations |
| CL023 | Learning-guided pricing reduces runtime, labels, pricing calls or final-judge effort | EV027 | None | TBD | Keep metric cells and prose conclusion `TBD` until frozen ablations exist | Any positive or negative performance conclusion | Future experiments |
| CL024 | Adding learned branch ranking improves the pricing-only learned variant | EV027 | None | TBD | Define paired ablation and decision rule only | Fabricated relative gain or expected win | Future experiments |
| CL025 | Learning generalizes to held-out maps or larger scales | EV027 | None | TBD | Specify held-out protocol, OOD checks and fail-safe fallback | Generalization, robustness or transfer claims | Future experiments |
| CL026 | The proposed method is the first learning-guided exact BPC for vehicle routing or lunar routing | EV026 | Insufficient | FORBIDDEN | Use a narrower evidence-backed contribution statement | “First,” “novel,” or “unprecedented” without exhaustive verification | Nowhere |
| CL027 | Learning guides cut generation, activation, retention or deletion | EV001, EV006, EV007 | Contradicted | FORBIDDEN | State the opposite boundary | Any learning-to-cut framing | Nowhere |
| CL028 | The optimized SRI benchmark demonstrates learning effectiveness | EV022–EV024, EV027 | Contradicted class | FORBIDDEN | Keep SRI optimization and future learning evidence separate | Re-label deterministic cut-engine results as GAT evidence | Nowhere |
| CL029 | Fixed-graph optimality implies optimality over arbitrary continuous lunar paths | EV009 | Contradicted scope | FORBIDDEN | Repeat the fixed logical-path solution space qualifier | Continuous-terrain global optimality | Nowhere |
| CL030 | Lunar south-pole prospecting and learning-assisted exact optimization are important current research contexts | EV026 | Context only | CITATION_REQUIRED | Support with primary/peer-reviewed external sources | Present project motivation as established fact without citations | Introduction; related work |

## Required Experiment Slots

| Slot | Comparison | Primary Metrics | Exact-Safety Gates | Evidence Status |
|---|---|---|---|---|
| EXP-L0 | Exact BPC without learning | wall time, labels, pricing/final-judge calls, nodes, closure | proof scope, objective, RC audit, no false exact | `TBD` |
| EXP-L1 | Exact BPC + learned pricing ordering | same as EXP-L0 plus inference overhead and fallback frequency | all EXP-L0 gates; no permanent negative drop; proof debt cleared | `TBD` |
| EXP-L2 | Exact BPC + learned pricing + learned branch-candidate ranking | same as EXP-L1 plus branch evaluations and child workload | valid candidate set preserved; complete fallback; same proofs | `TBD` |
| EXP-G | Held-out map/scale/OOD evaluation | closure, effort, inference, fallback and calibration | exact path unchanged under OOD fallback | `TBD` |

## Drafting Gate

No learning-performance sentence may move from `TBD` to `VERIFIED` until its
artifact path, configuration hash, split/leakage record, exact-safety audit and
measured value are added to `evidence_bank.md` and linked here.
