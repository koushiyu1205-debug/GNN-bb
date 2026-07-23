# Source Map

## Scope and Snapshot Boundary

- Project root: `/home/kai/work/GAT_BPC_moonTerk`
- PaperSpine workflow: `build_from_materials`
- Research snapshot date: 2026-07-23 (Asia/Shanghai)
- Target journal: *Transportation Research Part C: Emerging Technologies*
- Drafting state: motivation confirmed; Phase 1 evidence preparation and Phase
  2 section/paragraph blueprints completed; manuscript prose remains disabled.
- Post-snapshot run boundary:
  `runs/native_live_sri_v1_optimized_full80_paired_20260723/paired_run/`
  completed all 160 benchmark slots after the initial research snapshot. Its
  summary is admissible only as completed single-repeat, `benchmark_only`
  evidence. It is not a formal promotion experiment and does not authorize a
  production default switch.

## Evidence Authority

| Source ID | Authority | Path | Stable Role | Allowed Use | Forbidden Overclaim |
|---|---|---|---|---|---|
| E01 | A — frozen machine-readable evidence | `runs/native_spprc_no_cut_5_30_full3600_frozen_v1/baseline_freeze_manifest.json` and sibling summary/rows | Frozen no-cut control, instance/build/config provenance, 5/10/20/30 exact closure | Baseline correctness, timing distribution, reproducibility | Does not prove live SRI or current optimized engine |
| E02 | A — frozen machine-readable evidence | `runs/native_live_sri_v1_p0_frozen_paired_promotion_clean_v2_20260722/promotion_decision_manifest.json` and sibling rows/summary | 1040-slot fresh paired P0 experiment | P0 correctness and paired performance conclusions | P0 was `NOT_PROMOTED`; must not be described as production default |
| E03 | A — frozen machine-readable evidence | `runs/native_live_sri_v1_post_promotion_no_cut_50_100_bounded_regression_v2_signed_zero_fix_20260723/bounded_regression_summary.json` | 50/100 fail-closed safety evidence | Memory-limit blocker, zero proof leak/redlines | Not an exact-closure or optimal-time result |
| E04 | A — frozen machine-readable evidence | `runs/native_live_sri_v1_state_optimizations_20260723/state_optimization_summary.json` | Exact nonzero-dual projection and packed-overlap replay/diagnostic evidence | Exact-equivalence gates, controlled replay, one scale-20 diagnostic pair | Not a new promotion and not a default-switch result |
| E05 | A — frozen candidate definition | `runs/native_live_sri_v1_optimized_full80_paired_20260723/candidate_freeze_manifest.json` | Optimized candidate source/config/engine binding | Defines the candidate tested by the later completed benchmark-only run | The freeze artifact itself records `promotion_status=FROZEN_NOT_RUN`; performance conclusions require the separately qualified benchmark summary |
| E06 | B — mathematical contract | `plan/native_live_sri_v1_validity_and_certificate_boundary_zh.md` | SRI validity, Phase-I, reduced-cost audit, hash/lineage and proof scope | Formal method and proof-boundary description | Performance gates are not proof sources |
| E07 | B — implementation synthesis | `plan/native_live_sri_bpc_v1_implementation_report_zh.md` | Implemented loop, tests, frozen evidence and current recommendation | Current implemented algorithm and measured result map | Later engine results cannot be retroactively mixed with the old frozen promotion |
| E08 | B — current handoff | `plan/CODEX_HANDOFF_NATIVE_SPPRC_MAINLINE_20260722_ZH.md` | End-to-end solver flow, objective, scale evidence, GAT boundary, blockers | Reader-facing architecture and evidence routing | Handoff summaries do not outrank their machine-readable manifests |
| E09 | C — reviewed design input | `plan/native_live_sri_bpc_v1_review_zh.md` | Pre-implementation review, risk register and gate design | Motivation for safety contracts and experiment design | Review recommendations are not completed results |
| E10 | C — long-form design | `CODEX_lunar_gat_bpc_exact_algorithm_design.md` | Fixed logical-path solution-space model, pricing, branching, cuts, GAT safety shell | Definitions, design rationale and historical evolution | Design-only mechanisms must not be reported as active or validated |
| E11 | A — data provenance | `data/manifests/lunar_ice_sp50_real_benchmark_manifest.json` and `data/manifests/lunar_real_map_source_catalog.json` | Instance generation, map inputs, accepted cases and hashes | Dataset description and provenance | Fixed logical-graph results do not prove optimality over every continuous lunar path |
| E12 | B — figure assets | `runs/figures/basemaps/`, `runs/figures/task_sites/`, and scale-specific logical-graph figures | Existing map, terrain, resource, risk and task-site visuals | Candidate paper figures after provenance/caption audit | A visualization is not independent experimental evidence |
| E13 | C — completed benchmark-only evidence | `runs/native_live_sri_v1_optimized_full80_paired_20260723/paired_run/promotion_summary.json` and candidate freeze manifest | 160-slot, strict-cold, single-repeat paired benchmark of the optimized candidate | Candidate-bound correctness gates and explicitly qualified exploratory timing comparisons | `formal_design_complete=false`, `all_scales_promoted=false`, and `default_switch_allowed=false`; it is not a formal promotion or production-switch result |

## Controlling Fact Boundaries

1. **Current exact production method.** The released line is HiGHS restricted
   master + Native exact SPPRC pricing + Ryan–Foster branching with
   `live_sri_policy=no_cut`.
2. **Live SRI status.** SRI-3/SRI-5, active-cut Phase-I, lineage, dual/context
   binding and exact cut-state support are implemented. The first formal P0
   candidate passed correctness but failed the full performance promotion gate,
   especially at scale 30.
3. **Current optimized candidate.** Exact nonzero-dual projection and packed
   exact overlap state have passed controlled correctness/replay gates. The
   subsequent 160-slot paired run completed with all scale-local correctness
   and benchmark performance gates passing, but it used one repeat per
   mode/instance under `benchmark_only=true`. It may support a clearly labeled
   diagnostic comparison, not a formal promotion, production switch, or
   learning-performance claim.
4. **Scale boundary.** Frozen no-cut evidence closes 20 instances at each of
   scales 5, 10, 20 and 30. The 50/100 bounded runs are legal incomplete
   fail-closed results caused by an 8 GiB host-memory limit, not optimal solves.
5. **Objective boundary.** The official objective combines normalized operating
   cost, normalized risk and `0.4 * normalized_weighted_completion`; makespan is
   a reporting metric rather than another objective term.
6. **Fixed logical-path solution space boundary.** Current real-map instances
   use three fixed path options per directed logical edge. Exact claims are
   scoped to that fixed logical-path solution space, not the continuum of all
   possible lunar trajectories.
7. **Learning boundary.** The present guidance layer is an exact-safe
   shadow/ordering scaffold. It is not yet a trained GAT with demonstrated
   solver acceleration and does not supply bounds, pruning decisions or
   proofs.
8. **Confirmed paper mainline.** The manuscript must be organized as a
   pricing-led, branching-assisted learning-guided exact Branch-Price-and-Cut
   algorithm. Learning may prioritize pricing work and rank a limited set of
   branching candidates. It must not guide cut generation, selection,
   activation, retention or removal. Deterministic exact cut logic may remain
   part of BPC, while the exact path remains the sole source of official
   bounds, no-negative proofs, branch validity/completeness, pruning and
   optimality proofs. Missing learning-performance experiments will be
   represented by an explicit experiment protocol and `TBD` evidence slots,
   never by inferred or fabricated results.
9. **Terminology boundary.** Paper-facing prose uses `proof`/`prove`, fixed
   logical-path solution space, path-option space, state space and framework.
   `Certify`/`certified` is reserved for conclusions supported by an explicit
   derivation, exhaustive exact search or formal proof chain whose scope and
   responsible mechanism are stated. It must not describe learned scores,
   diagnostics, heuristic outputs, replay observations or benchmark gates.
   Literal code identifiers, enum values and file paths retain their original
   names. The controlling wording policy is `terminology_policy.md`.

## Research Routing

| Research Need | Primary Local Anchor | External Supplement Needed |
|---|---|---|
| Lunar south-pole water-ice exploration motivation | E11, E12 | Mission/science sources and recent lunar rover planning papers |
| Multi-sortie journey formulation | E08, E10 | Multi-trip/multi-graph VRP and energy-aware routing literature |
| Exact branch-price-and-cut architecture | E06, E07 | Recent BPC/column-generation papers and foundational pricing references |
| Learning-guided exact optimization | E08, E10 | Learning-to-price and learning-to-branch literature with exactness-preserving integration |
| Deterministic subset-row inequalities in live pricing | E06, E09 | SRI/cut-aware pricing literature; background only, never a learned-control contribution |
| Exactness and reproducibility | E01–E05 | Recent computational OR reporting and reproducibility norms |
| Target-journal rhetoric and structure | none | Six relevant TRC exemplars plus current official author guidance |
