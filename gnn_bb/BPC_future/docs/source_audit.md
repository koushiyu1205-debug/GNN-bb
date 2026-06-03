# BPC_future Source Audit

This directory is a new, self-contained experimental solver root. It does not import
legacy business modules from `bpc/` or `branchpricecut/`.

## Sources Reviewed

- `bpc/`: clean route-vehicle BPC, route pricing, route-set packing, task schedule-capacity cuts, RMP, branching, diagnostics.
- `branchpricecut/`: historical vehicle-schedule master, layered pricing, route pool, ng-DSSR experiments.
- `configs/`, `branchpricecut/config/`: current clean baseline and historical benchmark configurations.
- `tests/`: clean BPC regression tests and vehicle-schedule smoke tests.
- PDFs in the repository root:
  - Hernandez et al. 2014: trip-time master and time-occupation constraints.
  - Pessoa et al. 2020: ng-path, lm-rank1, path enumeration, smoothing, column cleanup.
  - Desaulniers et al. 2019: selective pricing exactness boundary.
  - You et al. 2023: BPC branching candidate testing cost.

## Migrated Ideas

- Hernandez-style timed trip columns and time occupation rows are the v1 master.
- Pessoa-style pricing-compatible design is retained as an interface boundary:
  cuts must be computable for future columns before they can become proof-relevant.
- Existing route-level `same_pool_degeneracy` diagnostics motivate avoiding
  finite-support route-signature cuts as a main strategy.
- Moon Trek preprocessing is separated from exact BPC: DEM/Slope rasters are
  downloaded, a deterministic risk grid is fixed, and only then should logical
  network costs be passed into the solver.

## Deliberately Not Migrated

- PersistentRMP and native pricing kernels.
- Legacy route-vehicle master `lambda[p,r]` as the main model.
- Finite-support weighted route-pack cuts as proof-strengthening mainline.
- Old solver imports from `bpc.*` or `branchpricecut.*`.

## v1 Exactness Boundary

The first implementation is exact for the configured grid-time trip universe. It
does not claim continuous-time optimality. A future version should replace grid
start enumeration with breakpoint pricing over continuous departure intervals.

Heuristic pricing, capped pricing, and interrupted pricing are column generators
only. They never certify a node. If exact grid pricing is not exhausted, the node
is logged as incomplete and the final status remains `TIME_LIMIT` unless another
complete proof is available.

The current restricted pool integer solve is a primal device. It can produce an
incumbent and can close a node only when its integer objective matches the exact
grid LP bound after exhausted pricing.
