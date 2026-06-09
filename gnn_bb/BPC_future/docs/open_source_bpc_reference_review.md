# Open-Source BPC Reference Review

Timestamp: 2026-06-08 23:20 CST

This note compares external Branch-Cut-and-Price, column-generation, VRP, and
learning-CG projects as architecture references for `BPC_future`. It is not a
code import plan. Do not copy external implementation code or add unclear
license obligations.

## Reference Projects

### Coluna.jl

Source: https://github.com/atoptima/Coluna.jl

- Master / RMP: organized around Dantzig-Wolfe decomposition over reformulated
  master formulations, with explicit separation between original model,
  master, subproblems, algorithms, and callbacks.
- Pricing / subproblem: pricing is a first-class algorithmic component rather
  than an incidental helper; the subproblem contract is clear about generated
  columns and bounds.
- Cuts / cut pool: cut handling is separate from pure column generation and is
  part of the algorithm orchestration layer.
- Branching / node processing: branch-cut-and-price is represented as a
  coordinated tree algorithm with callbacks and per-node processing.
- Stabilization / logging / certificate: stabilization is an algorithmic
  strategy, not a proof shortcut. The useful lesson for `BPC_future` is to keep
  stabilized/candidate duals distinct from the final certificate dual.
- Learning proof boundary: no learning component should be inferred from this
  framework; use it as a decomposition and state-machine reference only.

### VRPSolverEasy / VRPSolver

Source: https://github.com/inria-UFF/VRPSolverEasy

- Master / RMP: exposes a compact VRP-oriented modeling interface over an exact
  branch-cut-and-price engine.
- Pricing / subproblem: route generation is expressed through VRP resources,
  transitions, and graph/path abstractions, which is close in spirit to
  `BPC_future` journey-label pricing.
- Cuts / cut pool: exact VRP solvers treat cuts as solver-side state, not as
  ad-hoc pricing flags.
- Branching / node processing: the user interface hides most tree mechanics,
  but statuses and lower bounds remain explicit.
- Stabilization / logging / certificate: useful reference for concise exact
  VRP logging: instance, status, lower/upper bounds, elapsed time, and proof
  reason should be easy to read.
- Learning proof boundary: not a learning-CG reference.

### GCG

Source: https://github.com/scipopt/gcg

- Master / RMP: generic column generation and Dantzig-Wolfe reformulation are
  built on SCIP, with reformulation/detection logic separated from solving.
- Pricing / subproblem: pricing problems are independent SCIP models or
  solver components with clear lifecycle hooks.
- Cuts / cut pool: SCIP/GCG keep cuts, pricing, branching, and solving
  responsibilities separated through plugin-style components.
- Branching / node processing: node processing is solver-managed; column
  generation state must be compatible with branch constraints.
- Stabilization / logging / certificate: the relevant lesson is status
  discipline. A heuristic pricing miss is not an exact proof of no column.
- Learning proof boundary: no learning proof path; use it to validate
  `BPC_future` worker-vs-judge status semantics.

### COIN-OR Bcp

Source: https://github.com/coin-or/Bcp

- Master / RMP: classic branch-cut-price framework with explicit model,
  variable, cut, and tree-process concepts.
- Pricing / subproblem: column generation is a callback-style responsibility
  attached to node processing.
- Cuts / cut pool: cut pools and variable pools are separate architectural
  objects.
- Branching / node processing: branch decisions, node state, generated
  variables, and cuts have dedicated roles.
- Stabilization / logging / certificate: useful primarily as a separation of
  concerns reference; it is not a direct implementation model for the current
  Python direct-label oracle.
- Learning proof boundary: not applicable.

### COIN-OR SYMPHONY

Source: https://github.com/coin-or/SYMPHONY

- Master / RMP: classic callable branch/cut/price framework with problem
  classes and application callbacks.
- Pricing / subproblem: pricing is an application-provided module that fits
  into a larger tree-search engine.
- Cuts / cut pool: separates cut generation/management from LP solving.
- Branching / node processing: emphasizes clear tree state and callback
  contracts.
- Stabilization / logging / certificate: useful as a reminder that framework
  status and application subproblem status must not be conflated.
- Learning proof boundary: not applicable.

### RLCG

Source checked: https://github.com/khalil-research/RLCG

Note: the prompt listed
`https://github.com/chichengmessi/reinforcement-learning-for-column-generation`,
but unauthenticated `git ls-remote` could not access that repository in this
environment. The reviewed public learning-CG reference is `khalil-research/RLCG`.

- Master / RMP: learning experiments are organized around column generation
  loops and datasets rather than exact BPC proof.
- Pricing / subproblem: relevant only as a reference for data collection,
  policy inputs, and experiment reproducibility.
- Cuts / cut pool: not a reference for exact cut management.
- Branching / node processing: not a reference for exact tree proof.
- Stabilization / logging / certificate: useful for separating training logs,
  candidate-selection quality, and solver metrics.
- Learning proof boundary: learning can guide candidate generation or ranking
  only. It must never participate in official `BPC_future` lower bounds or
  optimality certificates.

## Gap Analysis For BPC_future

What is already strong:

- `BPC_future` has an explicit journey-column RMP and a manual true-RC formula
  in `manual_journey_reduced_cost`.
- Direct-label / completion-bound pricing already has a path toward exact
  true-dual certification.
- The current design docs already state that GNN dual anchors and worker-local
  no-column outcomes cannot certify global optimality.
- Final judge diagnostics already include useful harvesting and completion
  timing fields.

Where the current code is fragile:

- Pricing result semantics remain too compact for debugging hard tails:
  `FOUND_NEGATIVE`, worker-local no-column, duplicate-only, label-limit, and
  true certificate must be distinct in logs and driver decisions.
- Hidden-negative audit is not yet rich enough to explain why a profile or
  streaming worker missed a direct-label negative journey.
- Final judge can become an expensive worker: it may return a small number of
  replacement-only columns after a long proof search, causing RMP small-step
  updates and repeated tail calls.
- Learning, zero-reference, and stabilized dual centers need prominent
  "candidate only" tags in logs so they cannot be mistaken for proof inputs.

Safe ideas to migrate:

- Framework-style separation between master, pricing workers, final judge,
  cuts, branching, and node status.
- Explicit status enums and reason fields for pricing results.
- Batch column harvesting after expensive exact searches.
- Compact lower-bound / certificate logs that show which oracle produced the
  proof.
- Learning experiment organization: data collection, model version, candidate
  effect, and exact proof effect must be logged separately.

Ideas not suitable for direct migration:

- Do not copy external source code.
- Do not import or vendor code with unclear or incompatible licensing.
- Do not replace the true-dual direct-label certificate with a heuristic,
  learning policy, profile catalog, or local no-column result.
- Do not reuse dual-dependent pricing cache results unless the invalidation
  key covers the full dual/cut/branch/resource state that made the pruning
  decision valid.
- Do not turn framework-level abstractions into a broad rewrite before the
  current 5-task and 10-task performance envelope is frozen.

## Exactness Rules

- Official node lower bound and `OPTIMAL` certificate require
  `CERTIFIED_NO_NEGATIVE` from the true-dual direct-label / completion-bound
  final judge.
- `LOCAL_NO_COLUMN_UNCERTIFIED` is worker evidence only.
- Harvesting can return many negative columns, but it cannot prove that no
  other negative column exists.
- GNN / learning / tail dual center / zero-reference can influence early or
  mid candidate generation only unless an LP proves the dual is certificate
  equivalent to the true RMP dual.
