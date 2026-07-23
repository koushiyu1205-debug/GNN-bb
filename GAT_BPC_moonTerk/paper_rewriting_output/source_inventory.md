# Source Inventory

## Inventory Policy

- Snapshot date: 2026-07-23 (Asia/Shanghai)
- Materials root: `/home/kai/work/GAT_BPC_moonTerk`
- Method: curated emulation of PaperSpine's recursive material inventory.
- Machine inventory companion:
  `paper_rewriting_output/material_inventory.md` is the exhaustive
  script-generated file/path inventory required by the PaperSpine integrity
  audit. This curated `source_inventory.md` remains the reasoning-facing
  authority because it classifies evidence maturity and paper use.
- Reason for emulation: the repository contains approximately 13 GB of raw
  maps, build products, caches, and per-slot run artifacts. Recursively listing
  every file would obscure the paper-bearing sources without improving
  traceability.
- Selection rule: retain controlling configuration, confirmed scope, formal
  design contracts, executable algorithm entry points, frozen or explicitly
  bounded experiment summaries, dataset provenance, and candidate figures.
- Exclusion rule: omit caches, compiled objects, temporary logs, duplicate
  per-slot outputs, raw raster payloads, and generated environments. Their
  controlling manifests or summary artifacts remain inventoried.

## Authority Levels

| Level | Meaning |
|---|---|
| A | Frozen or machine-readable evidence suitable for verified factual claims |
| B | Mathematical, algorithmic, or implementation contract suitable for method claims after code consistency checks |
| C | Design, diagnostic, benchmark-only, review, or visualization material requiring explicit qualification |
| D | Missing, mutable, deprecated, or non-paper-bearing material |

## Paper-Bearing Materials

| ID | Path or Group | Type | Role | Authority | Status | Intended Paper Use |
|---|---|---|---|---|---|---|
| S001 | `paper_rewriting_output/paper_spine_config.json` | JSON | Workflow and output contract | A | active | Language, target, evidence and no-fabrication constraints |
| S002 | `paper_rewriting_output/confirmed_motivation.md` | Markdown | User-confirmed scientific and algorithmic mainline | A | confirmed | Pricing-led, branching-assisted learning-guided exact BPC scope |
| S003 | `paper_rewriting_output/research_dossier.md` | Markdown | Target, literature and research synthesis | B | complete | Introduction and positioning support; not project-result evidence |
| S004 | `paper_rewriting_output/citation_support_bank.md` | Markdown | Candidate external citations | B | complete | Citation routing for background and discussion |
| S005 | `paper_rewriting_output/sota_gap_map.md` | Markdown | Novelty-risk and gap map | B | complete | Claim calibration and contribution positioning |
| S006 | `CODEX_lunar_gat_bpc_exact_algorithm_design.md` | Markdown | Long-form exact algorithm design | B | current design | Formal definitions, proof ownership, fixed logical-path solution space scope |
| S007 | `plan/01_B0_Direct_DP_Frozen_Oracle.md` | Markdown | Frozen direct exact oracle contract | B | current | Small-scale reference and equivalence boundary |
| S008 | `plan/02_B1_BPC_Core_Root_Baseline.md` | Markdown | Root BPC contract | B | current | RMP, reduced cost and root closure description |
| S009 | `plan/03_B2_Pricing_Tail_Optimization_Layer.md` | Markdown | Exact pricing-tail contract | B | current | Native exact SPPRC and fail-closed completion logic |
| S010 | `plan/04_B3_Branch_and_Price_Tree_Layer.md` | Markdown | Branch-and-price contract | B | current | Ryan-Foster branching and completeness fallback |
| S011 | `plan/05_B4_Cut_Formulation_Layer.md` | Markdown | Deterministic cut/formulation contract | B | current | Exact cut validity and pricing compatibility; never learned cut control |
| S012 | `plan/06_B5_GAT_Guidance_Layer.md` | Markdown | Learning-guidance safety contract | B | scaffold design | Pricing/branch ordering semantics and proof-debt safeguards |
| S013 | `plan/native_live_sri_v1_validity_and_certificate_boundary_zh.md` | Markdown | Live-SRI validity and proof boundary | B | implemented contract | Deterministic SRI validity, cut-aware reduced cost and proof records |
| S014 | `plan/native_live_sri_bpc_v1_implementation_report_zh.md` | Markdown | Implementation/evidence synthesis | B | current synthesis | Architecture and evidence routing; manifests outrank it |
| S015 | `plan/CODEX_HANDOFF_NATIVE_SPPRC_MAINLINE_20260722_ZH.md` | Markdown | Current solver handoff | B | current synthesis | End-to-end flow, objective and production boundary |
| S016 | `src/lunar_ice_bpc/exact/master/journey_rmp.py` | Python | Restricted master implementation | B | implemented | Method and implementation traceability |
| S017 | `src/lunar_ice_bpc/exact/bpc/pricing/labeling_pricer.py` | Python | Exact labeling-pricer interface | B | implemented | Pricing algorithm and status semantics |
| S018 | `src/lunar_ice_bpc/exact/bpc/pricing/backends/native_rcspp.py` | Python | Native exact-pricing bridge | B | implemented | Exact completion path and native binding |
| S019 | `native/lunar_spprc/include/lunar_spprc/native_pricer.hpp`; `native/lunar_spprc/src/native_pricer.cpp`; `native/lunar_spprc/src/pybind_module.cpp` | C++ | Native SPPRC engine | B | implemented | Label state, dominance, cut state and Python interface |
| S020 | `src/lunar_ice_bpc/exact/core/branching.py` and `src/lunar_ice_bpc/exact/bpc/solver/` branch modules | Python | Exact branching implementation | B | implemented | Candidate validity, child construction and fallback |
| S021 | `src/lunar_ice_bpc/exact/core/cuts.py`; `src/lunar_ice_bpc/exact/bpc/cuts/live_sri.py`; `src/lunar_ice_bpc/exact/bpc/cuts/cut_audit.py` | Python | Deterministic exact cut machinery | B | implemented, opt-in | SRI validity and audit; excluded from learned control |
| S022 | `src/lunar_ice_bpc/exact/bpc/certificates/` and `src/lunar_ice_bpc/exact/certificates/` | Python | Proof ledgers and proof scope | B | implemented | Official proof ownership |
| S023 | `src/lunar_ice_bpc/exact/bpc/guidance/shadow.py`; `src/lunar_ice_bpc/exact/bpc/solver/gat_guidance_solver.py` | Python | Typed guidance and ordering safety shell | B | shadow/opt-in scaffold | Defines allowed heuristic ordering and forbidden proof effects |
| S024 | `src/lunar_ice_bpc/guidance/graph_builder.py`; `src/lunar_ice_bpc/guidance/shadow_policy.py` | Python | Deterministic features and shadow policy | C | future-model scaffold | Feature interface only; not evidence of a trained model |
| S025 | `runs/native_spprc_no_cut_5_30_full3600_frozen_v1/baseline_freeze_manifest.json` and frozen siblings | JSON/CSV | Frozen no-cut exact baseline | A | frozen | Exact closure and timing evidence at scales 5, 10, 20 and 30 |
| S026 | `runs/native_live_sri_v1_p0_frozen_paired_promotion_clean_v2_20260722/promotion_decision_manifest.json` and siblings | JSON/CSV | Formal P0 paired promotion | A | frozen, not promoted | Correctness success and performance-gate failure, especially scale 30 |
| S027 | `runs/native_live_sri_v1_state_optimizations_20260723/state_optimization_summary.json` | JSON | Exact-safe state optimization audit | A/C | frozen diagnostic | State-size and replay-equivalence facts; not promotion evidence |
| S028 | `runs/native_live_sri_v1_optimized_full80_paired_20260723/candidate_freeze_manifest.json` | JSON | Optimized-candidate binding | A | frozen candidate | Source/config/engine identity for the subsequent benchmark |
| S029 | `runs/native_live_sri_v1_optimized_full80_paired_20260723/paired_run/promotion_summary.json` | JSON | Single-repeat paired benchmark | C | complete, benchmark-only | Qualified exploratory timing and correctness-gate evidence only |
| S030 | `runs/native_live_sri_v1_post_promotion_no_cut_50_100_bounded_regression_v2_signed_zero_fix_20260723/bounded_regression_summary.json` | JSON | Large-scale bounded safety run | A | frozen, legally incomplete | Fail-closed memory-limit behavior; no exact-closure claim |
| S031 | `data/manifests/lunar_ice_sp50_real_benchmark_manifest.json` | JSON | Benchmark-instance manifest | A | frozen/current | Instance counts, scales, policies and generator provenance |
| S032 | `data/manifests/lunar_real_map_source_catalog.json` | JSON | Lunar map source catalog | A | current | Map-layer provenance, native resolution and local availability |
| S033 | `data/instances/lunar_ice_sp50_{005,010,020,030,050,100}/` | JSON group | Fixed logical-graph instances | A | generated corpus | Instance-level model inputs; refer through manifest |
| S034 | `runs/figures/basemaps/` | PNG/PDF group | Terrain, resource, risk and illumination maps | C | candidate figures | Context figures after provenance and caption audit |
| S035 | `runs/figures/lunar_ice_sp50_020_instance_001*.svg` | SVG group | Logical graph, path options and target layout | C | candidate figures | Fixed-solution space and instance-structure illustration |
| S036 | `runs/figures/task_sites/` | PNG/PDF group | Task-site map overlays | C | candidate figures | Benchmark illustration after label/readability review |
| S037 | `参考文献/` | PDF/Bib/document group | User-local reference collection | B/C | local-first input | Literature verification; not project-result evidence |
| S038 | `paper_rewriting_output/reference_materials/` | document group | PaperSpine reference cache/index | B | complete/current | Traceable research sources and exemplar routing |
| S039 | `paper_rewriting_output/terminology_policy.md` | Markdown | Mandatory paper-facing terminology and restricted `certify` use | A | active | Proof, solution-space/state-space and framework wording boundary |

## Explicitly Missing Evidence

| Missing ID | Required Material | Current Status | Drafting Consequence |
|---|---|---|---|
| M001 | Frozen training dataset, split manifest and leakage audit for pricing guidance | `TBD` | No trained-model or generalization claim |
| M002 | Trained pricing-guidance checkpoint, feature schema and inference record | `TBD` | Learning mechanism may be described only as proposed design |
| M003 | Learned branch-ranking checkpoint and valid-candidate evaluation logs | `TBD` | Branch guidance remains design-only |
| M004 | Paired ablation: exact BPC vs pricing guidance vs pricing+branch guidance | `TBD` | No runtime, search-effort or solve-rate improvement claim |
| M005 | Inference overhead, fallback frequency, exact-equivalence and held-out-map/scale results | `TBD` | Performance and robustness subsections must remain protocol/placeholders |

## Excluded Non-Paper-Bearing Material

| Pattern | Reason | Controlling Replacement |
|---|---|---|
| `.git/`, `.venv/`, `__pycache__/`, `.pytest_cache/`, compiler caches | Environment/cache artifacts | Source files and frozen manifests |
| `build/`, compiled objects and local extension binaries | Rebuildable products | Native source plus candidate/baseline build hashes |
| `data/raw_maps/*.tif` and derived raster tiles | Large binary payloads | `lunar_real_map_source_catalog.json` and figure derivatives |
| Per-slot stdout/stderr and duplicate row artifacts under completed runs | Excessively granular and partly redundant | Frozen summary, row table, manifest and hash chain |
| Temporary progress files from completed runs | Monitoring state, not final evidence | Final summary and decision/boundary fields |
