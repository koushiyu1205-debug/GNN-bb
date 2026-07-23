# Lunar Routing and Exact-Method SOTA Seed

This is a seed for gap mapping, not a claim that the final gap is already
established.

| ID | Work | Existing Capability | Comparison Boundary |
|---|---|---|---|
| SOTA001 | Chen et al. (2025), `10.1016/j.actaastro.2025.07.059` | Orders lunar science waypoints and plans feasible terrain/illumination/communication-aware trajectories | Uses a two-step genetic-algorithm mission planner; the current project instead studies exact fleet/journey routing on a fixed logical path-option space |
| SOTA002 | Lamarre et al. (2024), `10.1109/AERO58975.2024.10521136` | Chance-constrained mission-level planning with random faults and safe reachability | Strong risk-aware single-rover mission planning; not an exact multi-vehicle set-partitioning/BPC result |
| SOTA003 | Lamarre et al. (2023), `10.1016/j.actaastro.2023.09.028` | Recovery policies for solar-powered PSR exploration | Establishes safety/recovery importance but addresses stochastic reach-avoid planning rather than exact visit assignment and routing |
| SOTA004 | Mazarico et al. (2023), `10.1016/j.actaastro.2022.12.023` | Mostly sunlit pre-determined pathways between lunar south-pole sites | Supports illumination-aware network construction; does not solve the project’s fleet/journey optimization problem |
| SOTA005 | Breitfeld and Wettergreen (2024), IEEE Aerospace | Robust local trajectory planning for the MoonRanger water-ice mission | Local navigation and hazard avoidance are complementary to, not substitutes for, mission-level routing |
| SOTA006 | Jia et al. (2025), `10.1016/j.cja.2024.103388` | Large-scale lunar route optimization using a multi-level map | Relevant large-map heuristic/robust routing comparator; exact proof scope differs |
| METHOD001 | Cabrera et al. (2023), `10.1016/j.trc.2023.104369` | Branch-price-and-cut with tailored pricing, subset-row inequalities and optimality proofs | Closest method reference; route physics and lunar resource constraints differ |
| METHOD002 | Bezzi et al. (2023), `10.1016/j.trc.2023.104374` | Exact branch-and-price for route columns with partial recharge plans | Closest energy/recharge exact-routing reference; current columns are multi-sortie journeys on fixed lunar path options |
| LEARN001 | You et al. (2026), `10.1287/opre.2023.0615` | Two-stage learned branching inside exact BPC for CVRP and VRPTW | Directly rules out claiming that learning-guided exact VRP BPC is new by itself; the defensible gap must be application-, formulation-, interface-, or proof-boundary-specific |
| LEARN002 | Gasse et al. (2019), NeurIPS | Graph neural imitation of exact branch-and-bound branching decisions | Supports graph-based solver guidance, but does not establish performance or correctness for column generation, lunar routing, or this project |
| LEARN003 | Khalil et al. (2016), `10.1609/aaai.v30i1.10080` | Learning-to-rank surrogate for strong branching | Establishes the general learned branching lineage; exact solver logic remains responsible for correctness |
| LEARN004 | Tang et al. (2020), PMLR 119 | Reinforcement-learning policy for cutting-plane selection | Excluded-direction reference only: the confirmed paper does not use learned cut control |
| LEARN005 | Puigdemont et al. (2024), PMLR 235 | Learned cut-removal policies | Excluded-direction reference only: cut lifecycle decisions remain deterministic |

## User-Selected Mainline and Novelty Guardrail

The confirmed manuscript mainline is **pricing-led, branching-assisted
learning-guided exact branch-price-and-cut for lunar water-ice exploration
routing**. “Learning-guided” is an algorithm-control role: it may prioritize
pricing work and rank branching candidates. It must not control cut generation,
selection, activation, retention, or removal. It does not own lower bounds,
negative-reduced-cost exhaustion, branch validity/completeness, node pruning,
or the final optimality proof.

Because `LEARN001` is a direct learning-to-branch exact-BPC precedent, the
research must not claim to be the first learning-guided exact BPC or the first
learning-guided exact BPC for vehicle routing. A potentially defensible gap is
the proof-preserving integration of pricing guidance and secondary
branch ranking with the project’s fixed logical-path solution space lunar multi-sortie/fleet
formulation and native exact SPPRC/BPC machinery. Deterministic live SRI may be
part of the exact framework but is not a learned contribution. That gap remains
a hypothesis until the completed literature map and implemented learning
module support it. Missing learning experiments will be represented only as
protocols and `TBD` evidence slots.
