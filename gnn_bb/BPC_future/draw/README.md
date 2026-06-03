# Moon Trek Drawings

This folder contains visualization and scenario-sampling utilities for the
Moon Trek 20 km x 20 km patches.

The full data/model pipeline, including physical shortest paths, logical graph
construction, and the `low_time` / `low_energy` / `low_risk` path-option policy,
is documented in `BPC_future/docs/bpc_future_model_design.md`.

Run:

```bash
cd /home/kai/work/gnn_bb
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/draw/draw_moon_trek_patch.py
```

For the smoother Mare Crisium patch:

```bash
cd /home/kai/work/gnn_bb
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/draw/draw_moon_trek_patch.py \
  --terrain-dir BPC_future/data/moon_trek/crisium_smooth_20km
```

For the Balmer-like Mare Tranquillitatis patch:

```bash
cd /home/kai/work/gnn_bb
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/draw/draw_moon_trek_patch.py \
  --terrain-dir BPC_future/data/moon_trek/tranquillitatis_balmer_like_20km
```

To build physical-grid and logical-task graph figures:

```bash
cd /home/kai/work/gnn_bb
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_terrain_graph.py \
  --terrain-dir BPC_future/data/moon_trek/tranquillitatis_balmer_like_20km \
  --scenario BPC_future/draw/scenarios/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_region_seed7_tasks20.json \
  --grid-size 256
```

Outputs:

```text
BPC_future/draw/figures/
  apollo15_terrain_atlas.png
  apollo15_terrain_atlas.pdf
  apollo15_risk_map.png
  apollo15_risk_map.pdf
  apollo15_passability_map.png
  apollo15_passability_map.pdf
  apollo15_sample_scenario_seed7.png
  apollo15_sample_scenario_seed7.pdf
  apollo15_passability_map_seed7.png
  apollo15_passability_map_seed7.pdf

BPC_future/draw/scenarios/
  apollo15_region_seed7_tasks20.json
```

Sampling rule:

- The operational region is a radius-10 km circle inside the 20 km x 20 km patch.
- The depot is fixed at the center `(10.0, 10.0)` km. Only task points are
  randomized in later samples.
- The depot and tasks are sampled from passable cells.
- Tasks must be in the same 4-connected passable grid component as the depot.
- Every sampled task must satisfy the Euclidean screen:
  `2 * distance(depot, task) <= vehicle_max_roundtrip_km`.

This Euclidean screen is only a first feasibility guard for instance generation.
The final logical network must still compute physical risk-aware paths and check
energy, time, and route feasibility.
