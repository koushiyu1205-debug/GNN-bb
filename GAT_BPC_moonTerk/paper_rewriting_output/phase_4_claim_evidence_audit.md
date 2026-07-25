# Phase 4 Claim--Evidence Audit

## Audit Standard

A manuscript claim passes only when its wording matches the maturity of its
source. `FROZEN RESULT` supports recorded numerical facts; `IMPLEMENTED`
supports algorithm description; `DESIGN` supports intended behavior but not
effectiveness; `DIAGNOSTIC` and `BENCHMARK-ONLY` require an adjacent qualifier;
`TBD` supports no result sentence.

## Major-Claim Audit

| Claim | Manuscript Location | Evidence | Allowed Status | Audit |
|---|---|---|---|---|
| Orbital/near-infrared evidence and Chang'E-5 samples motivate candidate-site prospecting but do not establish site-level abundance, physical occurrence or accessibility in the benchmark region | Section 1 | C054, C061, C062; EV026; CL038 | Cited scientific context with explicit inference boundary | `PASS`; returned-sample evidence is not transferred to south-pole abundance or routing feasibility |
| The problem is mission-level multi-trip fleet routing | Abstract, Sections 1 and 3 | EV002, EV010--EV011; C041, C042, C054, C055 | Formulation/context | `PASS` |
| The common 50 km by 50 km region and configured higher-mobility regime are forward-looking benchmark assumptions rather than current rover capabilities | Sections 1 and 3 | EV010--EV011, EV032; CL036 | Bounded benchmark design | `PASS`; the qualification is adjacent to the first numerical extent statement |
| Permanently shadowed cold traps, rims and surrounding access terrain motivate candidate-site/path trade-offs without implying that all lunar water is confined to PSRs | Abstract, Sections 1, 2.1 and 3.1 | C042, C054, C055; EV011, EV032; CL037 | Cited application context plus project-proxy boundary | `PASS`; exclusivity and ground-truth claims are expressly excluded |
| Earlier completion of higher-science-weight tasks is the operational interpretation of the third objective term, not an ownership, race or makespan claim | Abstract, Sections 1 and 3.3 | EV003, EV028; LS08 | Implemented objective interpretation | `PASS`; no territorial or named time-sensitive framing appears |
| Exactness is limited to the fixed logical-path solution space | Abstract, Sections 1, 3, 7, 8 | EV009; CL005 | Proof-scope boundary | `PASS` |
| Lunar terrain, illumination, PSR, crater, steep-slope and elevation summaries are preprocessing inputs, while uncalibrated mixing coefficients are not presented as optimization-model equations | Section 3.1, Eq. (1) and adjacent scope paragraph | EV029; CL032 | Implemented generator provenance with physical-fidelity boundary | `PASS` |
| Same-endpoint path options removed before native labeling have a retained componentwise no-worse substitute with unchanged task, cut and branch coefficients | Section 3.1; Lemmas 1 and 3 | EV029, EV031; Native option filter | Exact-safe preprocessing | `PASS`; the reduced dominance representation is explicitly connected to full node-LP closure |
| The one-rover route universe, node route set and feasible fleet-schedule solution space use distinct symbols, and \(\bar S=|\mathcal T|\) is a nonrestrictive trip-slot bound | Sections 3.1--3.3 | EV029, EV031; CL032 | Formulation completeness | `PASS` |
| Core trip-level MILP families cover depot/task flow, activation, task count and uniqueness, binary domains, elementarity, temporal propagation, resource limits, recharge and trip sequencing; they are embedded in feasible multi-trip route columns rather than omitted from the algorithm | Section 3.2, Eqs. (4a)--(7), and Section 4.3 constraint-to-label table | EV029; CL032; `gurobi_compact.py`; Native SPPRC | Implemented compact equivalent and pricing semantics | `PASS` |
| The sole objective is normalized operating cost + normalized risk + 0.4 times normalized science-weighted completion time | Sections 1, 3, 8 | EV003, EV028; CL002, CL031; EQ-05 | Implemented/frozen | `PASS` |
| Trip risk, cost, shadow, energy, completion and positive normalization references match exact column construction | Sections 3.2--3.3, Eqs. (6b)--(10) | EV029; CL032 | Implemented formulation | `PASS` |
| Makespan is reporting-only | Section 3.3 | EV003; EQ-07 | Model boundary | `PASS` |
| Multi-trip route columns represent compatible trip schedules | Section 3.2 | EV002--EV003 | Implemented formulation | `PASS` |
| Native SPPRC is the exact pricing-completion path | Sections 4.3 and 4.7 | EV004--EV005 | Implemented proof contract | `PASS` |
| A learned score never proves absence of a negative column | Sections 1, 2, 4, and 7 | EV004--EV005, EV008 | Exact-safety boundary | `PASS` |
| Learning guides pricing first | Sections 1, 4.6.2, 5, and 7 | Confirmed motivation; EV001, EV008 | Design only | `PASS`; no effectiveness verb |
| Learning ranks exact-valid branch candidates second | Sections 1, 4.6.3, 5, and 7 | Confirmed motivation; EV007--EV008 | Design only | `PASS`; validity precedes score |
| Learning does not guide cuts | Sections 1, 2, 4.1, 4.4, and 5.4 | EV001, EV006 | Design/implementation boundary | `PASS` |
| Bounds, pruning, and termination remain exact-path responsibilities | Sections 4.1 and 4.7 | EV004--EV008 | Proof contract | `PASS` |
| Resource, dominance, completion-bound and node-bound pruning appear only with their exact/context guards | Sections 4.1 and 4.3, equations (14), (16)--(18) | EV030; CL033 | Implemented/context-bounded | `PASS` |
| Harvest guidance changes ordering only after true-negative and addability checks | Section 4.2, equation (15) | EV030; CL033 | Implemented exact shell + design ordering | `PASS` |
| Root-only SRI-3 validity and violation follow a predefined deterministic policy, while Ryan--Foster branching and deferred-pricing conditions retain their diagnostic/proof boundaries | Sections 4.4, 4.5 and 4.7, Eqs. (20)--(23) | EV030; CL033 | Implemented with explicit maturity bounds | `PASS` |
| The complete algorithm has a conditional mathematical exactness proof covering canonical routes, master equivalence, full node-LP closure, valid cuts, exact child partitions, guidance invariance and closed-tree induction | Section 4.7, Lemmas 1--5, Theorem 1 and Eqs. (24)--(27) | EV031; CL035 | Conditional proof within fixed paths and exact arithmetic | `PASS`; incomplete states and numerical tolerances remain explicitly qualified |
| Every delayed pricing item is registered before its true reduced cost is known and remains a proof obligation until rechecked, processed or covered by context-matched exhaustive repricing | Section 4.6.2, Eq. (23), Algorithm 2 | EV030, EV031 | Exact-safety interface | `PASS`; the \(\bar c_d=\bot\) case and prose now have the same semantics |
| Variables/changing indices are italic and fixed labels/operators are upright | All displayed mathematics; notation register | CL034; official Elsevier style guidance | Editorial conformance rule | `PASS` |
| The no-cut baseline closed 20 instances at each scale 5/10/20/30 | Abstract and Section 6.1 | EV014 | Frozen result | `PASS` |
| Baseline timing values in Table 1 are frozen evidence | Section 6.1 | EV014 | Frozen result | `PASS` |
| Formal deterministic root-only SRI-3 passed correctness but was not promoted | Abstract, Sections 6.2 and 7 | EV015--EV018 | Frozen result with decision label | `PASS` |
| The scale-30 SRI performance gate failed | Section 6.2 | EV018 | Frozen negative result | `PASS` |
| Exact state projection/packing had zero replay reduced-cost mismatches | Section 6.3 | EV019--EV020 | Frozen audit result | `PASS` |
| The single timing pair is diagnostic rather than general performance evidence | Section 6.3 | EV021 | Diagnostic only | `PASS`; qualifier adjacent |
| Optimized-candidate ratios are exploratory and not promotion evidence | Appendix C | EV026 | Benchmark-only | `PASS`; four prohibitive status fields retained |
| Scale-50/100 records are legal incomplete memory-limited runs | Section 6.5 and Appendix D | EV022--EV025 | Frozen boundary result | `PASS` |
| Scale-50/100 runs do not establish infeasibility or exact closure | Section 6.5 and Appendix D | EV022--EV025 | Negative scope boundary | `PASS` |
| A trained pricing model exists | Nowhere | M002 missing | Forbidden | `PASS`; explicit placeholder only |
| A trained branch-ranking model exists | Nowhere | M003 missing | Forbidden | `PASS`; explicit placeholder only |
| Learning improves runtime, labels, nodes, or solve rate | Nowhere | M004--M005 missing | Forbidden | `PASS`; result slots empty |
| Learning preserves exactness empirically | Nowhere as a completed result | M004--M005 missing | Forbidden until audit | `PASS`; protocol only |
| Learning generalizes to held-out maps or scales | Nowhere | M005 missing | Forbidden | `PASS`; OOD slot empty |
| The framework is optimal over continuous lunar terrain | Nowhere | No supporting evidence | Forbidden | `PASS` |
| Solver evidence proves field productivity or scientific yield | Nowhere | No supporting evidence | Forbidden | `PASS` |
| The paper defines a territorial/resource-race or newly named time-sensitive exploration problem | Nowhere | User-prohibited framing | Forbidden | `PASS` |

## Citation-Key Audit

The manuscript cites exactly the 22 locked keys:
`C001`, `C002`, `C003`, `C008`, `C009`, `C020`, `C021`, `C022`, `C023`,
`C025`, `C028`, `C029`, `C030`, `C041`, `C042`, `C044`, `C054`, `C055`,
`C059`, `C060`, `C061`, and `C062`. Each is represented in the manuscript's draft
reference-key map. These references support context or method positioning, not
project result values.

## Verdict

**PASS for a Phase 4 working draft.** No current learning-performance claim is
unsupported. Final sentence-to-passage verification, BibTeX assembly, and
submission formatting remain later-stage tasks.
