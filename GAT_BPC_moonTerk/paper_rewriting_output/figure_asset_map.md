# Figure Asset Map

## Manuscript-Wide Objective Guard

Any objective label, axis, legend, table column, or caption must use only the
normalized operating cost + normalized risk + `0.4 ×` normalized
science-weighted completion-time objective. Makespan may appear only as a
separately labeled reporting metric. No legacy or alternative objective
formula may appear in a manuscript-facing visual.

## Readiness Vocabulary

| Status | Meaning |
|---|---|
| READY_FOR_LAYOUT | Existing asset is technically usable; caption and final journal sizing remain |
| CANDIDATE | Existing asset is relevant but requires selection, annotation or provenance review |
| REGENERATE | Existing asset should be regenerated for legibility, aspect ratio or consistent styling |
| TO_CREATE | Conceptual figure can be created from verified method structure without inventing data |
| TBD_EVIDENCE | Cannot be created until missing experimental evidence exists |

## Existing and Planned Figures

| Figure ID | Source Image or Data | Intended Caption | Target Location | LaTeX Label | Evidence Anchor | Readiness | Required Action |
|---|---|---|---|---|---|---|---|
| FIG01 | `paper_rewriting_output/figures/lunar_water_ice_exploration_schematic_v5.pdf` and `.png` | Five spatially registered lunar planning layers: LOLA shaded relief, DEM terrain, deterministic traversal-risk proxy, average solar visibility and an illustrative fleet route-selection layer | Problem context/model | `fig:lunar_environment_route_stack` | EV009–EV011 | READY_FOR_LAYOUT | Use the vector PDF for submission and the 500 dpi PNG for review; the caption distinguishes map-derived inputs, model proxies and visualization-only route selection |
| FIG02 | `runs/figures/basemaps/south_pole_sp50_preview_resource_basemap.pdf` and `.png` (2522×2254) | Water-ice resource-potential layer used by the benchmark generation pipeline | Data | `fig:resource_basemap` | EV011 | CANDIDATE | Use only if the atlas is too dense; identify proxy construction and avoid implying ground-truth ice abundance |
| FIG03 | `runs/figures/basemaps/south_pole_sp50_preview_risk_basemap.pdf` and `.png` (2522×2254) | Deterministic traversal-risk layer derived from recorded terrain inputs | Data/problem formulation | `fig:risk_basemap` | EV011 | CANDIDATE | Audit colorbar, units and exact derivation; distinguish model risk from observed mission risk |
| FIG04 | `runs/figures/basemaps/south_pole_sp50_preview_illumination_basemap.pdf` and `.png` (2522×2254) | Average solar-visibility context used in the benchmark map pipeline | Data | `fig:illumination_basemap` | EV011 | CANDIDATE | Confirm layer role in generator and caption native resolution; do not imply it enters every objective term |
| FIG05 | `runs/figures/lunar_ice_sp50_020_instance_001_logical_graph_dem.svg` (920×920) | A scale-20 fixed logical graph over lunar terrain, including the depot and task sites | Problem formulation | `fig:fixed_logical_graph` | EV009, EV010 | CANDIDATE | Inspect labels at one- and two-column widths; simplify or enlarge nodes; identify exact instance hash in caption |
| FIG06 | `runs/figures/lunar_ice_sp50_020_instance_001_path_options_dem.svg` (920×920) | Declared path alternatives on the fixed directed logical graph; exactness is restricted to these precomputed options | Problem formulation/exactness scope | `fig:fixed_path_space` | EV009 | CANDIDATE | Confirm the display distinguishes all three options per directed edge; add a fixed logical-path solution-space boundary annotation |
| FIG07 | `runs/figures/lunar_ice_sp50_020_instance_001_targets_dem.svg` (920×920) | Spatial distribution of the scale-20 exploration, detection, drilling and sampling targets | Data | `fig:task_targets` | EV010 | CANDIDATE | Check task-mode legend and color accessibility; avoid duplicating FIG05 |
| FIG08 | `runs/figures/task_sites/lunar_ice_sp50_020_instance_001_task_sites.pdf` and `.png` (2522×2254) | Task-site overlay for a representative scale-20 benchmark instance | Data | `fig:task_sites` | EV010, EV011 | REGENERATE | Review apparent viewer/aspect and label-density issue; crop whitespace and test journal-size readability before use |
| FIG09 | To create from EV002, EV004–EV007, and EV011 | End-to-end exact BPC architecture: map-derived fixed graph → journey RMP → learning-ranked pricing work → mandatory exact SPPRC completion → deterministic cut/branch context → exact proof ledger | Method overview | `fig:method_overview` | EV002, EV004–EV007, EV011 | TO_CREATE | Create a vector schematic; visually separate heuristic ordering from proof-bearing transitions; show no learning arrow into cut control |
| FIG10 | To create from EV001, EV004, EV005 and EV007 | Responsibility boundary between the learning layer and the exact path: pricing/branch ordering on the heuristic side, validity, completeness, bounds, pruning and proofs on the exact side | Exactness analysis | `fig:learning_exact_boundary` | EV001, EV004, EV005, EV007 | TO_CREATE | Use a two-lane diagram with explicit forbidden paths; no numerical claims |
| FIG11 | To create from EV002–EV006 | Exact node workflow with RMP solve, candidate ordering, fast pricing, true-dual completion, deterministic separation, branch fallback and proof decisions | Method | `fig:exact_node_flow` | EV002–EV006 | TO_CREATE | Keep status names consistent with code; show incomplete-limit fail-closed branch |
| FIG12 | To create from `baseline_summary.json` | Frozen no-cut cold-start runtime by scale, with distribution-aware summaries over 20 instances per scale | Experiments | `fig:baseline_scaling` | EV012–EV014 | TO_CREATE | Generate only from the frozen row table/summary; use log scale if appropriate; state descriptive, not causal, interpretation |
| FIG13 | To create from the formal P0 promotion manifest | Formal P0 live-SRI paired performance by scale, highlighting the scale-30 failed promotion gate | Experiments | `fig:p0_formal_promotion` | EV015–EV017 | TO_CREATE | Plot paired ratios and 95% intervals; show threshold and `NOT_PROMOTED`; keep separate from optimized-candidate benchmark |
| FIG14 | To create from the 160-slot optimized-candidate benchmark | Single-repeat benchmark-only paired ratios for the optimized deterministic SRI candidate | Appendix/exploratory results | `fig:optimized_sri_benchmark_only` | EV021–EV024 | TO_CREATE | Prominently label “benchmark-only, one repeat, not formally promoted”; do not combine estimates with FIG13 |
| FIG15 | Future learning ablation data | Exact BPC effort and time under no learning, pricing guidance, and pricing-plus-branch guidance | Learning experiments | `fig:learning_ablation` | EV027 | TBD_EVIDENCE | Wait for frozen EXP-L0/L1/L2 artifacts; predefine axes and metrics only |
| FIG16 | Future held-out/OOD data | Held-out map/scale behavior, fallback frequency and exact-closure outcomes | Robustness experiments | `fig:heldout_ood` | EV027 | TBD_EVIDENCE | Wait for split manifest, OOD definition and frozen results |

## Planned Tables

| Table ID | Source | Purpose | Evidence Anchor | Readiness |
|---|---|---|---|---|
| TAB01 | Model/design contracts and `objective.py` | Sets, variables, objective components, constraints and fixed logical-path solution-space scope | EV002, EV003, EV009 | READY_FOR_LAYOUT |
| TAB02 | `lunar_ice_sp50_real_benchmark_manifest.json` | Corpus counts, scales, fleet/task settings and generation policies | EV010 | READY_FOR_LAYOUT |
| TAB03 | `lunar_real_map_source_catalog.json` | Map layers, roles, native resolution and local availability | EV011 | READY_FOR_LAYOUT |
| TAB04 | Frozen no-task-wait exact-control summary | Exact counts and scale-wise mean/p50/max strict-cold time under root-only SRI-3 | EV036–EV037 | READY_FOR_LAYOUT |
| TAB05 | Formal P0 promotion decision | Correctness, performance gates, paired estimates and final status by scale | EV015–EV017 | READY_FOR_LAYOUT |
| TAB06 | State-optimization summary | Projection rule, state bytes and replay-equivalence audit | EV018–EV020 | READY_FOR_LAYOUT |
| TAB07 | Bounded scale-50/100 summary | Resource limit, terminal status and proof blockers | EV025 | READY_FOR_LAYOUT |
| TAB08 | Future EXP-L0/L1/L2 artifacts | Learning ablation including overhead, fallback, pricing and branching effort | EV027 | TBD_EVIDENCE |

## Selection Recommendation Before Drafting

The likely main-text set is FIG01, FIG09, FIG10, FIG12 and FIG15,
plus TAB01, TAB02, TAB04 and TAB08. FIG13 is suitable if deterministic SRI
remains an important exact-engine component in the paper; FIG14 belongs in an
appendix unless a formal repeated promotion is later completed. This is a
layout recommendation only, not authorization to generate result figures from
`TBD` data.
