# Moon Trek Preprocessing

`BPC_future/preprocess/` builds a deterministic physical-risk layer before the
optimization model runs. The exact BPC solver consumes fixed logical arc costs;
it does not call risk prediction during pricing.

Two supported presets use NASA Moon Trek raster services:

- `apollo15`: DEM `LRO_NAC_DEM_26N004E_150cmp`, slope
  `LRO_NAC_Slope_15m_26N004E_150cmp`.
- `balmer_flat`: DEM `LRO_NAC_DEM_19S070E_150cmp`, slope
  `LRO_NAC_Slope_15m_19S070E_150cmp`.
- `crisium_smooth`: DEM `ApolloZone_MetricCam_DEM_Global_1024ppd`; slope is
  derived once from this DEM during preprocessing.
- `tranquillitatis_balmer_like`: DEM `ApolloZone_MetricCam_DEM_Global_1024ppd`;
  slope is derived once from this DEM. The patch was selected to keep
  Balmer-like slope statistics without NAC strip gaps.

The default patch is approximately 20 km by 20 km around Apollo 15:

```text
center lon/lat = 3.4384, 26.10935
pixels         = 2048 x 2048
```

Run:

```bash
cd /home/kai/work/gnn_bb
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_moon_trek_patch.py
```

For the flatter Balmer Basin patch selected by a coarse slope screen:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_moon_trek_patch.py \
  --site balmer_flat
```

For the smoother Mare Crisium patch, which avoids NAC strip gaps:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_moon_trek_patch.py \
  --site crisium_smooth
```

For the Balmer-like Mare Tranquillitatis patch:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_moon_trek_patch.py \
  --site tranquillitatis_balmer_like
```

Outputs are stored under:

```text
BPC_future/data/moon_trek/<patch>/
  raw/dem.tif
  raw/slope.tif
  metadata/bbox.json
  metadata/moon_trek_sources.json
  metadata/download_manifest.json
  processed/risk_grid.npz
  processed/risk.tif
  processed/impassable.tif
  processed/risk_metadata.json
```

The v1 risk model is deterministic:

```text
risk = 0.75 * (slope / impassable_slope)^2
     + 0.25 * min(local_dem_std / roughness_reference, 1)
```

Cells with slope greater than or equal to `30 deg` are marked impassable. These
rules are deliberately simple and auditable. A later model can replace the risk
formula as long as the preprocessing output remains fixed before BPC starts.

Visualization and scenario sampling live in `BPC_future/draw/`:

```bash
cd /home/kai/work/gnn_bb
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/draw/draw_moon_trek_patch.py
```

For Crisium:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/draw/draw_moon_trek_patch.py \
  --terrain-dir BPC_future/data/moon_trek/crisium_smooth_20km
```

For Tranquillitatis:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/draw/draw_moon_trek_patch.py \
  --terrain-dir BPC_future/data/moon_trek/tranquillitatis_balmer_like_20km
```

The draw script produces DEM/Slope/Risk figures and a reproducible sampled
20-task operational region. The sampler fixes the depot at `(10.0, 10.0)` km,
uses a radius-10 km circle, requires every task to be in the same 4-connected
passable component as the depot, and rejects task sets where any task violates
the configured vehicle roundtrip distance screen relative to the depot.

After terrain and task sampling, `build_terrain_graph.py` constructs a
deterministic lower graph:

```text
terrain risk grid -> downsampled 8-neighbor physical graph
                  -> all-pairs depot/task shortest paths
                  -> logical graph with distance, risk, time, energy proxy, and cost
```

Example:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_terrain_graph.py \
  --terrain-dir BPC_future/data/moon_trek/tranquillitatis_balmer_like_20km \
  --scenario BPC_future/draw/scenarios/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_region_seed7_tasks20.json \
  --grid-size 256
```
