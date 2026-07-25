# Section Writing Input Packets

## Use Contract

This file is a structured pre-draft input, not manuscript prose. A section may
be drafted only after the user explicitly authorizes that section. Drafting
must proceed paragraph-row by paragraph-row against
`writing_rationale_matrix.md`.

Every paragraph must satisfy all of the following:

1. one registered paragraph function;
2. one or more allowed claim IDs;
3. a project-evidence anchor for project-specific statements;
4. a verified external citation for contextual/comparative statements;
5. the same scope qualifier carried by any associated figure or table;
6. no activation of a `TBD` result slot;
7. no first-person construction.

## Front Matter Packet

| Item | Frozen Input |
|---|---|
| Paragraph rows | FM01–FM06 |
| Purpose | Name the lunar fleet-routing problem, fixed logical-path solution space, exact BPC framework, learned ordering actions, proof ownership, and bounded evidence status |
| Allowed claims | CL001–CL012, subject to maturity; no learning-effect claim |
| Project evidence | EV001–EV011 |
| Citation inputs | C041, C042, C054, C055 for application; C001, C002 for nearest learned precedents if needed |
| Required result input | Abstract result sentence remains `TBD` until EXP-L0/L1/L2/G are frozen |
| Visuals | none |
| Forbidden | “first,” speedup, solved-scale headline, trained-GAT implication, learned cuts, continuous-terrain optimality |
| Entry gate | final learning results available or an explicitly provisional abstract is requested |
| Exit gate | title, abstract, keywords reproduce the same mainline and evidence maturity as the body |

## Section 1 — Introduction Packet

| Item | Frozen Input |
|---|---|
| Paragraph rows | I01–I06 |
| Purpose | Move from lunar prospecting as a coupled transportation decision to the scoped integration and validation gap |
| Allowed claims | CL001, CL005, CL009–CL012, CL030; CL002–CL008 only at high level |
| Project evidence | EV001, EV002–EV011, EV027 |
| Core citations | C041, C042, C044, C054, C055; C022, C025; C020, C021, C028–C030, C060; C001–C003, C008, C009, C059 |
| Visuals | none |
| Required qualifiers | fixed logical-path solution space; learning effects are hypotheses until tested; no learned cut control |
| Forbidden | universal novelty; mission deployment; field validation; learning-performance statement; asymptotic explanation inferred from scale timings |
| Entry gate | citation keys and support passages assigned sentence by sentence |
| Exit gate | reader can identify problem, solution scope, pricing-primary role, branching-secondary role, proof owner, and evidence gap |

## Section 2 — Related Work Packet

| Item | Frozen Input |
|---|---|
| Paragraph rows | RW01–RW10 |
| Purpose | Synthesize lunar planning, exact route-based optimization, and learning-guided exact search by decision/interface role |
| Allowed claims | CL005–CL012, CL026–CL030 as explicit novelty/scope controls |
| Project evidence | EV001, EV004–EV009, EV026–EV027; project evidence is used only to state the present paper's boundary |
| Core citations | Lunar: C041, C042, C044, C054, C055; exact routing: C020–C023, C028–C030, C060; learned search: C001–C003, C008, C009; pricing control: C059 |
| Citation cautions | C001 blocks a broad learning-guided exact-BPC novelty claim; C002 and C009 are learned pricing/control precedents, not no-negative proofs; C023 is branch-and-cut rather than BPC |
| Visuals | optional literature taxonomy table only |
| Forbidden | paper-by-paper chronology without synthesis; “no prior work”; treating selective pricing or learned discovery as exact exhaustion |
| Entry gate | `citation_lock.md` roles accepted |
| Exit gate | the remaining gap is application/interface/evidence-specific and testable |

## Section 3 — Problem Setting and Mathematical Formulation Packet

| Item | Frozen Input |
|---|---|
| Paragraph rows | P01–P09 |
| Purpose | Define graph, path options, trip/multi-trip-route hierarchy, resources, objective, master, and reduced cost |
| Allowed claims | CL001–CL005, CL013–CL014, CL031 |
| Project evidence | EV002–EV003, EV009–EV011, EV028 |
| Equations | EQ-01–EQ-10 in `model_notation_and_equation_register.md` |
| Citations | C041/C044 only for external path-planning context if needed; no external source may override implemented objective semantics |
| Visuals/tables | FIG01 or FIG06; TAB01–TAB03 |
| Mandatory objective wording | throughout the manuscript, use normalized operating cost + normalized risk + `0.4 ×` normalized weighted completion; makespan is report-only |
| Internal compatibility rule | legacy alpha/beta/gamma/delta fields are excluded from manuscript-facing text and remain only in the pre-draft schema audit |
| Forbidden | any alternative objective vocabulary or formula; mixing raw and normalized objective; representing a multi-trip route as a single trip; branch context as a dual term; continuous-path optimality |
| Entry gate | explicit user authorization to draft Section 3 |
| Exit gate | every symbol appears before use and maps to a source path; objective/master/pricing use one cost definition |

## Section 4 — Proposed Exact Learning-Guided BPC Packet

| Item | Frozen Input |
|---|---|
| Paragraph rows | M01–M20 |
| Purpose | Define the exact node loop, Native SPPRC, deterministic cuts, exact branching, learned interfaces, fallbacks, and proof proposition |
| Allowed claims | CL004–CL012; learning components remain `DESIGN_ONLY` |
| Project evidence | EV004–EV008, EV025, EV027 |
| Equations | EQ-10–EQ-12 plus source-backed label/resource transitions |
| Citations | C020, C021, C028–C030, C060; C001–C003, C008, C009, C059 |
| Visuals | FIG09–FIG11; feature/interface tables |
| Mandatory responsibility split | learning orders pricing and valid branch candidates; exact logic owns validity, cuts, exact completion, bounds, pruning, termination, and proofs |
| Mandatory status rule | incomplete or unsupported context fails closed; no heuristic/learned absence of a column is a proof |
| Forbidden | learning-to-cut; trained-model status; performance verbs; permanent learned deletion of required work; `NO_FRACTIONAL_RF_PAIR` as integrality |
| Entry gate | source-level interface and status names rechecked against current code |
| Exit gate | a reviewer can remove the learned ranking and recover the unchanged complete exact path |

## Section 5 — Experimental Design Packet

| Item | Frozen Input |
|---|---|
| Paragraph rows | E01–E11 |
| Purpose | Predefine research questions, corpus, data split, variants, comparators, training, safety gates, metrics, paired protocol, OOD evaluation, and four-phase seasonal comparison |
| Allowed claims | CL013–CL014; CL023–CL025 and CL039 only as neutral questions/protocols |
| Project evidence | EV010–EV012, EV015, EV021, EV025, EV027, EV033 |
| Citations | C001–C003, C008, C009, C059; C022/C025 for transportation evaluation context; C063 for polar-shadow epoch design |
| Tables | experiment matrix and TAB08 shell |
| Required variants | L0 exact BPC; L1 L0 + learned pricing ordering; L2 L1 + learned valid-branch-candidate ranking; no learned-cut variant |
| Required controls | frozen non-learning pricing schedules; identical exact path, budgets, instances, hardware, and proof gates |
| Missing inputs | M001–M006 remain `TBD`; M006 must freeze a southern-vernal-equinox reference, 12 anchors across one draconic year, four three-anchor phase labels, approximately 28.9-day spacing, scale-dependent 16–76 h windows, one-hour environmental samples, the window-aggregation rule, within-window variation audit and paired phase summaries |
| Forbidden | invented split, architecture, hyperparameter, checkpoint, sample count, expected effect, or comparator implementation |
| Entry gate | may be drafted as protocol only if user explicitly permits; empirical details stay `TBD` |
| Exit gate | every research question has a metric, baseline, safety gate, artifact field, and result slot |

## Section 6 — Computational Results Packet

| Item | Frozen Input |
|---|---|
| Paragraph rows | R01–R11E and R11 |
| Purpose | Report exact-framework evidence first, root-only SRI-3 evidence with maturity labels, then learning safety/effect/held-out evidence, four-phase seasonal evidence, and the resource boundary |
| Allowed existing claims | CL015–CL022 with their frozen, diagnostic, or benchmark-only qualifiers |
| Blocked claims | CL023–CL025 |
| Project evidence | EV012–EV025 available; EV027 blocks R06–R10; EV033/M006 block R11E |
| Visuals/tables | FIG12–FIG16; TAB04–TAB08 |
| Required ordering | exact framework → formal root-only SRI-3 → state/replay boundary → learning safety → pricing effect → incremental branch effect → heterogeneity/OOD → seasonal operating phases → resource limit |
| Forbidden | relabeling deterministic SRI results as learning evidence; merging formal P0 and benchmark-only candidate; interpreting incomplete 50/100 runs as solved |
| Entry gate | R01–R05/R11 may use frozen evidence after explicit permission; R06–R10 require M001–M005 and EXP artifacts; R11E requires M006 and EXP-EPOCH |
| Exit gate | all denominators, repeats, intervals, failures, overhead, fallback, and proof gates are visible |

## Section 7 — Discussion and Limitations Packet

| Item | Frozen Input |
|---|---|
| Paragraph rows | D01–D07 |
| Purpose | Interpret results in research-question order, explain mechanism, state transportation relevance, and preserve map/model/computation limits |
| Allowed claims | only result claims activated in Section 6 plus CL005, CL009–CL012, CL022 |
| Project evidence | EV004–EV011, EV025, EV033, and future frozen learning/epoch evidence |
| Citations | C022, C025, C039 if retained; C052–C055 and C063 for map/application/environment limitations |
| Mandatory limitations | fixed logical-path solution space; hourly states aggregated into per-epoch deterministic inputs/proxies; anchor spacing distinct from mission duration; no cross-epoch robustness or dynamic-optimality claim; scale-50/100 resource boundary; missing/unproven learning transfer |
| Forbidden | scientific-yield benefit without evidence; physical mission guarantee; post-hoc motivation; generalization from average runtime |
| Entry gate | corresponding result rows must be active |
| Exit gate | every implication includes tested condition, uncertainty, and transfer boundary |

## Section 8 — Conclusion Packet

| Item | Frozen Input |
|---|---|
| Paragraph rows | C01–C03 |
| Purpose | Restate the transportation problem, exact-safe interface, actual evidence, and bounded significance |
| Allowed claims | subset of claims already supported and discussed |
| Project evidence | no new evidence |
| Citations | normally none |
| Forbidden | new claim, new number, new limitation, “first,” learned-cut wording, diagnostic as headline |
| Entry gate | Sections 1–7 are evidence-complete |
| Exit gate | the conclusion does not outrun the abstract, results, or fixed exactness scope |

## Appendix and Caption Packet

| Item | Frozen Input |
|---|---|
| Paragraph rows | APP01–APP04; CAP01–CAP03 |
| Appendix A | full notation, resource transitions, assumptions, and proof proposition; must match EQ register |
| Appendix B | root-only SRI-3 validity and formal negative promotion, separate from learning |
| Appendix C–D | benchmark-only candidate and legal-incomplete scale boundary with qualifiers in headings/captions |
| Appendix E | M001–M006 lineage, split/checkpoint/schema/run hashes, extended ablations, OOD records, and paired seasonal-phase manifest/results |
| Caption contract | learning uses “rank/order”; exact path uses “validate/prove”; `TBD` visuals have no direction-implying colors/arrows |
| Forbidden | estimated placeholder numbers; maturity qualifier only in surrounding prose but absent from caption |

## Draft Activation Ledger

All rows remain `PENDING`. A later draft action changes only the rows explicitly
authorized by the user. Completion of this input package does not itself change
any row to `DRAFTED` or `PASS`.
