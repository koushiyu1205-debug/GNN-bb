# Contribution and Novelty Review

## Overall assessment

The manuscript presents a carefully bounded exact-optimization study for lunar south-pole water-ice prospecting. Its strongest aspect is the explicit separation between the finite logical-path model, deterministic exact conclusions, and learning-based search ordering. The multi-path, multi-trip route-column formulation with no waiting at task sites, depot departure adjustment, cumulative shadow exposure, charging, and science-weighted completion time is potentially valuable. The conditional exactness argument is also unusually transparent about incomplete pricing and numerical tolerances.

The submission is nevertheless incomplete as a contribution paper. The title and second contribution position learning-guided exact BPC as a central result, but the GAT comparison, calibration, and end-to-end evaluation remain placeholders. The computational value of the deterministic acceleration components is likewise not yet separated. Moreover, the literature review does not establish sufficiently precisely which part of the model or algorithm is new relative to the closest multi-trip VRPTW, multi-path routing, electric-vehicle BPC, and learning-guided column-generation studies. The paper therefore has a promising technical framework, but its novelty and significance are not yet supported at the level required for publication.

## Scores

| Dimension | Score | Justification |
|---|---:|---|
| Contribution clarity | 4/5 | Section 1 states three contributions and Sections 3–4 define the model, exact algorithm, learning permissions, and proof boundary clearly. Clarity is reduced because established BPC components and genuinely new elements are bundled together in Contribution 2. |
| Novelty | 3/5 | The integration of no-task-wait multi-trip scheduling, finite terrain-path alternatives, lunar resource attributes, and an exact-safe learning interface appears potentially novel. However, Sections 2.1–2.3 do not yet demonstrate this differentiation against the closest formulations and algorithms, and several algorithmic components are standard. |
| Evidence-to-claim strength | 2/5 | The deterministic closure counts and conditional proof support a limited exact-solvability claim. The central learning result, deterministic component ablations, and multi-epoch results are not available, while the claimed proof-tail bottleneck and reproducible benchmark are not yet fully evidenced in the manuscript. |
| Venue appropriateness | 4/5 | Exact vehicle routing, learning-assisted optimization, time-window scheduling, and emerging autonomous-mobility applications fit *Transportation Research Part C*. The paper should more clearly extract transferable routing and algorithmic insights beyond the lunar case. |

## Major findings

### 1. The genuinely new contribution is not sufficiently separated from established BPC machinery

Section 1, Contribution 2 describes bidirectional negative-column search, batch column admission, root-node SRI-3 cuts, exhaustive pricing, Ryan–Foster branching, and constrained label ordering as one contribution. Sections 2.2 and 4 acknowledge that SRI-3, Ryan–Foster branching, route columns, and resource-constrained pricing are established components, but the manuscript does not identify which mathematical or algorithmic element is the primary novelty.

The paper should explicitly distinguish at least three layers: established BPC machinery; adaptations required by the no-task-wait multi-trip lunar model; and the new learning action surface. A closest-work comparison should cover multi-path routing, multi-trip VRPTW, charging-aware route columns, exact BPC, and learning-guided pricing. For each closest study, it should state whether it includes alternative physical paths, cross-trip resource propagation, task-site no-wait timing, cumulative environmental exposure, exhaustive exact fallback, and learned label ordering. Without this comparison, the novelty score remains provisional.

### 2. The learning-guided contribution is methodologically specified but not empirically established

Sections 4.6 and 5.4 define a conservative GAT interface and credible activation conditions. This is a strength: the model cannot alter feasibility, dominance, reduced costs, bounds, pruning, or termination. However, Section 6.3 contains only an author placeholder. There is currently no evidence that the permitted local ordering space contains useful headroom, that GAT improves over linear or MLP baselines, or that inference and fallback overhead do not offset any pricing benefit.

This gap affects the title, abstract, Section 1 Contribution 2, and the conclusion. Before the learning-guided algorithm can serve as a principal contribution, the paper needs the predeclared queue controls, common-split Linear/MLP/GAT comparison, independent calibration, held-out replay, and paired end-to-end BPC evaluation with identical exact outcomes. If these experiments do not establish incremental value, the paper should be reframed as an exact BPC with a proof-preserving learning interface rather than as a demonstrated learning-guided acceleration.

### 3. The computational value of the deterministic innovations is not isolated

Table 2 in Section 6.1 reports only the complete deterministic BPC. Section 6.2 explicitly leaves the component results to be filled. Consequently, the current evidence supports exact closure counts and observed runtime for the combined implementation, but it does not show whether bidirectional search, batch admission, or root-only SRI-3 screening provides a benefit, imposes overhead, or shifts work elsewhere.

The paired ablation proposed in Sections 5.3 and 6.2 is necessary. It should report exact-closure counts together with root bounds, column-generation rounds, accepted columns, exhaustive-pricing calls, processed labels, memory, and total time. Runtime comparisons should include incomplete cases rather than conditioning only on commonly solved instances. These results are essential because the deterministic components currently carry most of the algorithmic evidence while the learning evaluation is unfinished.

### 4. Model significance needs comparison against simpler formulations, not only solution-time reporting

Sections 3.1–3.3 make a plausible case that alternative terrain paths, no waiting at task sites, multiple depot-to-depot trips, shadow exposure, and science-weighted completion time jointly matter. The experiments, however, do not yet show how much these modeling choices change feasibility, task completion order, selected paths, or objective components. At present, the lunar features are well described mathematically but their decision value is asserted rather than demonstrated.

A model-focused experiment should compare at least selected variants such as single-path versus multi-path, wait-permitted versus no-task-wait timing, and single-trip versus multi-trip planning on matched instances. Sensitivity to the fixed coefficient 0.4 and to the normalization references in Equation (11) is also important. The objective weight is central to the scientific-priority interpretation, but the manuscript currently gives no robustness evidence for it. These analyses would convert the lunar application from a contextual relabeling concern into a demonstrated transportation-planning contribution.

### 5. One discussion claim exceeds the evidence currently shown

Section 7.2 states that the main scaling difficulty has shifted from finding feasible columns to the proof tail of exhaustive pricing. Section 6.1 establishes that five 50-task runs ended with incomplete pricing, but it does not provide a decomposition showing that initial or intermediate column discovery was no longer limiting. This diagnosis requires pricing-phase telemetry, time-to-first-incumbent or time-to-accepted-column data, and proof-tail time or label-memory measurements. Until those data are reported, the sentence should be softened to say that the incomplete-run records *suggest* a proof-tail bottleneck.

### 6. Reproducibility and novelty verification remain prospective

Section 1 calls the instances reproducible, whereas Section 5.5 says that code, generation configurations, data-source manifests, and per-instance records “will be provided.” The contribution should be phrased prospectively until these artifacts are actually supplied and sufficient to regenerate the benchmark. Similarly, the working citation keys in the manuscript do not allow an external reviewer to verify the claimed gap against the cited literature. A final reference list and stable artifact manifest are required before the novelty and reproducibility claims can be fully assessed.

## Strengths to preserve

- Sections 3.3 and 4.7 clearly limit exactness to the fixed, finite logical-path solution space and distinguish exact arithmetic from implementation tolerances.
- The fail-closed treatment of incomplete pricing and incomplete branching is rigorous and avoids converting diagnostics into certificates.
- The separation of hard shadow-exposure feasibility, energy feasibility, and risk preference gives the lunar model a clearer physical interpretation than a single blended environmental penalty.
- Section 5 predeclares sensible paired comparisons, leakage controls, non-graph baselines, fallback reporting, and survivor-bias safeguards.

## Recommendation

**Major Revision.** The formulation and proof framework are promising and relevant to the venue, but the paper's central learning-guided contribution and the value of its deterministic components have not yet been empirically established. A revised submission should complete the planned ablations and learning evaluation, sharpen differentiation from the closest literature, demonstrate the decision value of the lunar-specific modeling choices, and align reproducibility and bottleneck claims with supplied evidence.
