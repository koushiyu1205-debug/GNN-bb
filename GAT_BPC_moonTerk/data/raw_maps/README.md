# Real Lunar Map Inputs

This directory is the local landing zone for real lunar south-pole raster data.
The first real-map preview pipeline does not modify the BPC instance generator;
it checks these files, auto-selects a defensible high-illumination depot near
the lunar south pole, crops a `50 x 50 km` ROI centered on that depot, and draws
map/data readiness previews.

Expected first-pass LOLA files:

| Local filename | Role |
| --- | --- |
| `LOLA_80S_dem_80m.tif` | Optional DEM/elevation layer for directed uphill/downhill path costs. |
| `LOLA_80S_hillshade.tif` | Terrain context background. |
| `LOLA_80S_slope_100m.tif` | Required terrain-risk layer; the current PGDA GeoTIFF reports 1000 m pixels. |
| `LOLA_80S_roughness_100m.tif` | Required terrain-risk layer; the current PGDA GeoTIFF reports 1000 m pixels. |
| `LOLA_80S_psr_20m.tif` | Required PSR / shadow layer. |
| `AVGVISIB_85S_060M_201608.tif` | Recommended illumination layer for peak-of-eternal-light depot scoring. |

Optional later layers:

| Local filename | Role |
| --- | --- |
| `DIVINER_south_pole_temperature.tif` | Thermal-risk layer. |
| `M3_water_proxy_south_pole.tif` | Surface OH/H2O proxy. |
| `LEND_hydrogen_proxy_south_pole.tif` | Coarse hydrogen proxy. |

Run:

```bash
python scripts/download_lunar_real_maps.py --dry-run --print-curl
python scripts/download_lunar_real_maps.py --probe-only --layers required
python scripts/download_lunar_real_maps.py --layers lola_dem
python scripts/download_lunar_real_maps.py --layers lola_avg_solar_visibility
python scripts/draw_lunar_real_map_preview.py
```

If network access to PGDA is stable, the download helper can fetch the required
LOLA files directly:

```bash
python scripts/download_lunar_real_maps.py --layers required
```

If the required LOLA files are missing, the command writes a fail-closed preview
manifest with `status=MISSING_REQUIRED_REAL_MAP_LAYERS` and does not use a
synthetic fallback.
