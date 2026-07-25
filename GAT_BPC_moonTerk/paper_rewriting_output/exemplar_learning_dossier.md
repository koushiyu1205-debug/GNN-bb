# Exemplar Learning Dossier

This dossier initially used indexed metadata and structural reasons. The
formatting update below records the one exemplar manuscript that was later
inspected directly. Uninspected full texts remain ineligible as evidence for
formats, wording, or performance.

## Verified Component-Algorithm Format Update

The open manuscript of Cabrera, Cordeau, and Mendoza's TRC branch-price-and-cut
paper was inspected on 2026-07-24:
<https://chairelogistique.hec.ca/wp-content/uploads/2023/02/Parkandloop.pdf>.
Its pricing section presents small component procedures as separately numbered
algorithms with `Require` and `Ensure` declarations, numbered pseudocode lines,
and a following paragraph that explains the roles of line ranges. This
presentation pattern, rather than any problem-specific algorithm content, is
transferred to Section 4 of the working manuscript. Algorithms 1--3 now expose
the node loop, guidance-ordered pricing with exact completion, and
exact-valid branch ranking in that format.

## Verified Formulation-Placement Update

Three TRC route-based exact papers were checked specifically for the placement
of compact constraints, route definitions, master rows, and pricing logic.

- Cabrera, Cordeau, and Mendoza place route feasibility and the route master in
  Section 2, then place column generation, pricing, valid inequalities, and
  branching in Section 3. Their pricing subsection defines the elementary
  resource-constrained path construction rather than repeating the formulation.
  Source:
  <https://chairelogistique.hec.ca/wp-content/uploads/2023/02/Parkandloop.pdf>.
- Bezzi, Ceselli, and Righini introduce the feasible route set and route master
  in Section 3, “Mathematical formulation,” before developing the pricing
  algorithms. Internal energy and recharge feasibility is encoded by the
  feasible-route definition and recovered through dynamic programming rather
  than restated as master rows. Sources:
  <https://doi.org/10.1016/j.trc.2023.104374> and
  <https://air.unimi.it/bitstream/2434/1049821/2/53%20-%202023%20TRC%20-%20EVRP%20route%20based.pdf>.
- Sakarya et al. first give the original arc-based formulation, including
  route flow, service, capacity, inventory, synchronization, and variable
  domains, in Section 4. Section 5 then derives the route master and pricing
  problems by decomposition. Sources:
  <https://doi.org/10.1016/j.trc.2024.104987> and
  <https://pure.tue.nl/ws/portalfiles/portal/349454819/1-s2.0-S0968090X24005084-main.pdf>.

The transferable placement rule is therefore: define the full semantics of a
feasible route or column in the problem/formulation section; state the compact
original formulation there when it is needed for clarity; place the
set-partitioning or set-covering master at the formulation/decomposition
boundary; and use the pricing section to explain the constructive enforcement
of route-local constraints through states, transitions, dominance, and
completion. The working manuscript follows this pattern by placing the core
route-local families in Section 3.2 and a constraint-to-label correspondence in
Section 4.3.

## Exemplar Inventory

| Title | Venue | Year | Why selected |
|---|---|---:|---|
| A route-based algorithm for the electric vehicle routing problem with multiple technologies | Transportation Research Part C (TRC) | 2023 | Route formulation and pricing |
| Solving the park-and-loop routing problem by branch-price-and-cut | TRC | 2023 | Closest BPC/SRI analogue |
| Two-echelon prize-collecting vehicle routing with time windows and vehicle synchronization | TRC | 2025 | Complex constraints and implications |
| An exact algorithm for unpaired pickup and delivery vehicle routing problem with multiple commodities and multiple visits | TRC | 2024 | Inequalities, real-case evaluation, sensitivity |
| Adaptive robust electric vehicle routing under energy consumption uncertainty | TRC | 2024 | Uncertainty and operational trade-offs |
| Coordination of drones at scale | TRC | 2023 | Sensing, system relevance, open data |

## Structural Patterns

**Bezzi, Ceselli, and Righini.** The indexed arc begins with a technology-driven routing problem, defines extended routes, develops exact pricing, and evaluates computational value. This suggests a title joining the application class and algorithmic device, and an abstract mirroring problem–formulation–algorithm–evidence.

**Cabrera, Cordeau, and Mendoza.** The closest exact-method model links nonstandard route composition to a set-covering master, tailored pricing, subset-row inequalities, and explicit proofs. Each BPC component can therefore be explained through the structural obstacle it resolves, with proof production visible in the experimental narrative.

**Sakarya et al.** Multiple trips, replenishment, time windows, and synchronization are framed as one transportation system. The indexed emphasis on design and managerial implications suggests closing experiments by translating model behavior into operational choices tied to tested scenarios.

**Xu et al.** The recorded progression is operational pain point, model, valid inequalities, exact algorithm, real-case comparison, and sensitivity analysis. It supports an introduction narrowing to a mathematical gap, methods separating formulation strengthening from exact search, and experiments moving from solvability to interpretation.

**Jeong et al.** Energy-consumption uncertainty is connected to reliability through robustness and trade-off analysis. The transferable move is to introduce a resource constraint through its operational consequence, state the protection mechanism precisely, and interpret sensitivity results as trade-offs rather than universal performance claims.

**Qin and Pournaras.** Autonomous sensing is linked to transportation-system coordination, scale, and energy awareness, with open-data evaluation explicitly indexed. This suggests making the transportation relevance of lunar sensing fleets explicit and giving dataset provenance and availability a visible role in the experimental design.

Across the six exemplars, three reusable moves recur in the inventory: couple the title and abstract to both the transportation problem and solution class; let the introduction narrow from system need to a precise modeling or algorithmic gap; and organize methods and experiments around traceable obstacles, exactness mechanisms, comparisons, robustness or sensitivity checks, and operational interpretation.

## Rhetorical Patterns

A strong opening moves from a concrete transportation-system consequence to the constraint or decision that existing formulations do not adequately represent. A strong closing returns to that consequence, states what the evidence establishes, and separates operational implications from limitations and untested extensions.

## Language Patterns

Use formal, compact, mechanism-centered prose. Define BPC, pricing resources, inequalities, and proof sources before evaluation; distinguish exact proof-producing paths from learned guidance or diagnostics. Prefer bounded verbs such as “formulates,” “evaluates,” and “proves,” and describe open data through verifiable provenance and availability rather than promotional claims.
