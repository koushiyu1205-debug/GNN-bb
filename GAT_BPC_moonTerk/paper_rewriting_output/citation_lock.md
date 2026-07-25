# Core Citation Lock

## Lock Status

- Target: at least 20 core references
- Locked count: 24
- Verification date: 2026-07-24
- Purpose: fix each reference's allowed argumentative role before body drafting.
- Rule: “verified” means that publisher/journal/institutional metadata or a
  primary paper record was located. It does not mean that every full-text
  passage has already been assigned to a final sentence.

Crossref API access was unavailable in the execution environment. Verification
therefore used official publisher, journal, mission, institutional, or primary
paper pages. Final BibTeX export and sentence-level passage checks remain part
of the later citation-insertion step.

## Locked Set

| ID | Reference and Stable Locator | Verification | Allowed Support | Must Not Support |
|---|---|---|---|---|
| C041 | Chen, Jackson, Allard, and Beltrame, “Path planning algorithm for a South Pole lunar rover mission,” 2025. [DOI](https://doi.org/10.1016/j.actaastro.2025.07.059) | Official ScienceDirect page verified | Waypoint ordering and terrain/illumination/communication-aware lunar path planning | Exact fleet BPC, learning performance, or project validation |
| C042 | Lamarre, Malhotra, and Kelly, “Safe Mission-Level Path Planning for Exploration of Lunar Shadowed Regions by a Solar-Powered Rover,” 2024. [Primary preprint](https://arxiv.org/abs/2401.08558), [DOI](https://doi.org/10.1109/AERO58975.2024.10521136) | Primary manuscript and conference DOI metadata verified | Chance-constrained mission-level lunar planning under illumination, faults, and safe reachability | Multi-rover exact journey optimization or project result |
| C044 | Mazarico et al., “Sunlit pathways between south pole sites of interest for lunar exploration,” 2023. [DOI](https://doi.org/10.1016/j.actaastro.2022.12.023) | Official ScienceDirect page verified | Precomputed south-pole paths and illumination-aware traversal context | Current model's exactness or performance |
| C054 | Sefton-Nash et al., “Targeting Intermittently Sunlit Areas With Thermal Stability for Buried Water Ice in the South Polar Region of the Moon,” 2026. [DOI](https://doi.org/10.1029/2025JE008985) | Official AGU/Wiley page verified | Scientific and operational relevance of thermally stable water-ice candidate regions | Ground-truth validation of project resource/risk proxies |
| C055 | NASA, “VIPER Lunar Operations.” [Official page](https://science.nasa.gov/mission/viper/lunar-operations/) | Official NASA page verified | Terrain, illumination, temperature, power, communication, and route-planning motivation | Algorithmic novelty, exactness, or solver performance |
| C061 | Zhou et al., “Chang'E-5 samples reveal high water content in lunar minerals,” 2022. [DOI](https://doi.org/10.1038/s41467-022-33095-1) | Official Nature Communications article and full text verified | Returned-sample evidence that mineral composition, structure, and exposure history affect solar-wind-derived lunar surface water | South-pole site abundance, path feasibility, or benchmark calibration |
| C062 | He et al., “A solar wind-derived water reservoir on the Moon hosted by impact glass beads,” 2023. [DOI](https://doi.org/10.1038/s41561-023-01159-6) | Official DOI metadata and institutional full-text record verified | Returned-sample evidence that impact glass beads can host solar-wind-derived lunar surface water | South-pole resource abundance, operational accessibility, or routing performance |
| C063 | Kloos, Moores, Sangha, Nguyen, and Schorghofer, “The temporal and geographic extent of seasonal cold trapping on the Moon,” 2019. [DOI](https://doi.org/10.1029/2019JE006003) | Official AGU/Wiley article and full text verified; journal is indexed in SCIE Q1 in the relevant category | Temporal and geographic variability of lunar polar seasonal shadow; 12-lunation hourly illumination study; equinox/solstice seasonal interpretation; dependence on local topography and time of year; rationale for independently window-aggregated mission epochs | A routing-horizon prescription, a claim that every local shadow changes slowly, that one instantaneous environmental state is valid throughout every mission window, that the current optimizer is departure-time dependent, that Kloos et al. identify a fastest routing phase, or that the planned multi-epoch experiment is complete |
| C064 | Wei, Li, Zhang, Tian, Jiang, Wang, and Ma, “Illumination conditions near the Moon's south pole: Implication for a concept design of China's Chang'E-7 lunar polar exploration,” 2023. [DOI](https://doi.org/10.1016/j.actaastro.2023.03.022) | Official ScienceDirect article and Crossref metadata verified; Acta Astronautica is indexed in SCIE and was JCR Q1 in Engineering, Aerospace | Operational relevance of time-dependent and particularly seasonal polar illumination; southern-summer illumination analysis near Shackleton crater; seasonal conditioning for landing, solar-power and traverse design | A prescribed four-phase grouping, a cross-season routing comparison, a fastest-season conclusion, transfer of the 15 km by 15 km site extent, or support for BPC exactness |
| C022 | Sakarya et al., “Two-Echelon Prize-Collecting Vehicle Routing with Time Windows and Vehicle Synchronization: A Branch-and-Price Approach,” 2025. [DOI](https://doi.org/10.1016/j.trc.2024.104987) | Official publisher metadata verified | Coupled multi-fleet, replenishment, time-window, and synchronization decisions | Lunar application validity or BPC-cut novelty |
| C025 | Qin and Pournaras, “Coordination of drones at scale: Decentralized energy-aware swarm intelligence for spatio-temporal sensing,” 2023. [DOI](https://doi.org/10.1016/j.trc.2023.104387) | Official ScienceDirect page verified | Energy-aware coordinated movement for spatio-temporal sensing as a transportation-system analogue | Exact routing proof or learning-guided BPC precedent |
| C020 | Cabrera, Cordeau, and Mendoza, “Solving the park-and-loop routing problem by branch-price-and-cut,” 2023. [DOI](https://doi.org/10.1016/j.trc.2023.104369) | Official publisher/institutional metadata verified | Tailored pricing, subset-row inequalities, branching, and exact reporting in a complex routing BPC | Project-specific cut validity or performance transfer |
| C021 | Bezzi, Ceselli, and Righini, “A route-based algorithm for the electric vehicle routing problem with multiple technologies,” 2023. [DOI](https://doi.org/10.1016/j.trc.2023.104374) | Publisher-linked transport record verified | Route columns encoding resource-management and recharge decisions | Lunar journey equivalence or project proof |
| C023 | Xu et al., “An exact algorithm for unpaired pickup and delivery vehicle routing problem with multiple commodities and multiple visits,” 2024. [DOI](https://doi.org/10.1016/j.trc.2024.104488) | Official ScienceDirect page verified | Exact-algorithm reporting, valid inequalities, branching, and operational analysis | Branch-price-and-cut or pricing precedent; the method is branch-and-cut |
| C028 | Lera-Romero, Miranda Bront, and Soulignac, “A branch-cut-and-price algorithm for the time-dependent electric vehicle routing problem with time windows,” 2024. [DOI](https://doi.org/10.1016/j.ejor.2023.06.037) | Official ScienceDirect page verified | Multi-resource exact pricing and tailored labeling under time-dependent energy/travel | Project dominance correctness or learning benefit |
| C029 | Nafstad, Desaulniers, and Stålhane, “Branch-Price-and-Cut for the Electric Vehicle Routing Problem with Heterogeneous Recharging Technologies and Nonlinear Recharging Functions,” 2025. [DOI](https://doi.org/10.1287/trsc.2024.0725) | Official INFORMS page verified | Tailored BPC and bidirectional labeling for rich recharge behavior | Lunar model proof or performance transfer |
| C030 | Yuan, Cui, and Baldacci, “An exact algorithm for a mobile production vehicle routing problem,” 2025. [DOI](https://doi.org/10.1016/j.tre.2025.104255) | Official ScienceDirect page verified | Journey/route columns encoding coupled internal operations and branch-price-and-cut | Direct lunar or learning-guided precedent |
| C060 | Poggi and Uchoa, “New Exact Algorithms for the Capacitated Vehicle Routing Problem,” 2014. [SIAM chapter](https://epubs.siam.org/doi/10.1137/1.9781611973594.ch3) | Official SIAM page verified | Foundational exact VRP, column-generation, and branch-cut-and-price lineage | Current project correctness or novelty |
| C001 | You, Yang, Wang, and Yin, “Two-Stage Learning to Branch in Branch-Price-and-Cut Algorithms for Solving Vehicle Routing Problems Exactly,” 2026. [DOI](https://doi.org/10.1287/opre.2023.0615) | Official INFORMS page verified | Direct learning-to-branch precedent inside exact vehicle-routing BPC; novelty guardrail | Claim that this paper is the first learning-guided exact BPC |
| C002 | Abouelrous et al., “Reinforcement learning for solving the pricing problem in column generation for routing,” 2025. [DOI](https://doi.org/10.1016/j.orp.2025.100364) | Official ScienceDirect page verified | Learned pricing precedent and comparator | Proof of reduced-cost exhaustion or exact closure |
| C003 | Wang et al., “Learning to Branch in Combinatorial Optimization With Graph Pointer Networks,” 2024. [Journal issue](https://www.ieee-jas.com/article/2024/1), [DOI](https://doi.org/10.1109/JAS.2023.124113) | Official journal issue and primary manuscript verified | Graph/global/historical solver-state features for learned branching | Exact branch validity, completeness, or lunar transfer |
| C008 | Cappart et al., “Combinatorial Optimization and Reasoning with Graph Neural Networks,” JMLR 24(130), 2023. [Official JMLR page](https://jmlr.org/papers/v24/21-0449.html) | Official journal page verified | Broad distinction between direct neural optimization and neural enhancement of exact solvers | Project-specific effectiveness or exactness |
| C009 | Qu et al., “Enhancing column generation by reinforcement learning-based hyper-heuristic for vehicle routing and scheduling problems,” 2025. [DOI](https://doi.org/10.1016/j.cie.2025.111138) | Official ScienceDirect page verified | Learned control of column-generation heuristics and comparator design | No-negative-column proof; its heuristic pruning is not the present proof contract |
| C059 | Desaulniers, Galindo Pecin, and Contardo, “Selective pricing in branch-price-and-cut algorithms for vehicle routing,” 2019. [DOI](https://doi.org/10.1007/s13676-017-0112-9) | Publisher-version metadata and institutional record verified | Non-learning selective-pricing baseline and separation of relaxed/stronger pricing effort | Learned-method evidence or unconditional proof exhaustion |

## Role Totals

| Role | Count |
|---|---:|
| Lunar application and mission/path context | 8 |
| Transportation-system and complex-fleet framing | 2 |
| Exact route-based/BPC lineage and analogues | 7 |
| Learning-guided branching/pricing and GNN context | 5 |
| Non-learning pricing-control baseline | 1 |
| Total | 23 |

## Mandatory Citation Boundaries

1. C001 must appear wherever a broad “first learning-guided exact BPC” claim
   might otherwise arise.
2. C002 and C009 support learned pricing/control as precedents; neither may be
   used to prove exact column exhaustion in the present solver.
3. C023 supports exact-algorithm reporting and branch-and-cut structure, not
   BPC pricing.
4. C055 supports application motivation only and must not be treated as a
   peer-reviewed algorithmic source.
5. C059 is the required non-learning pricing-control comparator. Its corrected
   author list is Desaulniers, Galindo Pecin, and Contardo.
6. C061 and C062 support lunar-water occurrence and heterogeneity only. They
   do not establish water-ice abundance or accessibility at the benchmark's
   south-pole candidate sites.
7. C063 supports the temporal structure and variability of lunar polar shadow
   and the rationale for independently frozen mission epochs. It does not
   validate the benchmark horizon or establish slow change at every location.
8. No external reference supplies project results, objective coefficients, or
   proof records.

## Later Insertion Gate

Before a citation enters body text:

- the exact sentence claim must be written in the citation bank;
- a supporting abstract/full-text passage must be recorded;
- final bibliographic metadata and citation key must be exported;
- the source must be used only within its locked role;
- the citation must not be used as a substitute for project evidence.
