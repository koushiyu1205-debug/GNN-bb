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


  <!-- PYTHONDONTWRITEBYTECODE=1 /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future.py \
  --config BPC_future/configs/moon_trek_20_smoke.yaml \
  --time-limit 3600 \
  --results-csv BPC_future/results/probe_root_tail_zero_tasks20_pair_3600_budgetfix_20260608.csv \
  --log-dir BPC_future/results/logs_probe_root_tail_zero_tasks20_pair_3600_budgetfix_20260608 \
  --solution-dir BPC_future/results/solutions_probe_root_tail_zero_tasks20_pair_3600_budgetfix_20260608 \
  --set journey_dual_stabilization_enabled=True \
  --set journey_dual_stabilization_tail_only_enabled=True \
  --set journey_dual_stabilization_certificate_candidate_enabled=True \
  --set journey_dual_stabilization_mode=l1_reference \
  --set journey_dual_stabilization_reference_mode=root_tail_zero \
  --set journey_dual_stabilization_time_limit=0.5 \
  --instances \
  BPC_future/data/generated/moon_trek_60/logical_graphs/apollo15_20km/tasks_20/apollo15_20km_tasks20_02_seed21018_logical_graph.json \
  BPC_future/data/generated/moon_trek_60/logical_graphs/tranquillitatis_balmer_like_20km/tasks_20/tranquillitatis_balmer_like_20km_tasks20_01_seed21000_logical_graph.json \
  2>&1 | awk '
    /\[BPC_future/ && /(journey node|journey branch|journey fathom|finish)/ {
      print
      fflush()
    }
    /journey_pricing/ && /(exact_completion_bound|direct_label_partial_state_budget|CERTIFIED_NO_NEGATIVE|FOUND_NEGATIVE|time_limit)/ {
      print
      fflush()
    }
    /: status=/ || /BPC_future CSV written:/ || /Traceback|ValueError|Error/ {
      print
      fflush()
    }
  ' -->