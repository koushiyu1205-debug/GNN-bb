# Source Map

## Scope and Evidence Cutoff

- Project root: `/home/kai/work/GAT_BPC_moonTerk`
- PaperSpine workflow: `build_from_materials`
- Research evidence cutoff: 2026-07-23 (Asia/Shanghai)
- Target journal: *Transportation Research Part C: Emerging Technologies*
- Drafting state: motivation confirmed; Phase 1 evidence preparation, Phase 2
  section/paragraph blueprints, Phase 3 pre-draft freeze, and the Phase 4
  English working draft are complete. Missing learning artifacts and results
  remain explicit `TBD` blocks. Final LaTeX, Word, translation, and submission
  formatting are not part of Phase 4.
- Later-run boundary:
  `runs/native_live_sri_v1_optimized_full80_paired_20260723/paired_run/`
  completed all 160 benchmark slots after the initial research cutoff. Its
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
| E14 | B — executable model mathematics | `src/lunar_ice_bpc/domain/real_maps.py`; `exact/solver/gurobi_compact.py`; `exact/core/columns.py`; `exact/core/journey.py`; `exact/core/objective.py`; Native SPPRC option filter and visited-task state | Immutable lunar path inputs, same-endpoint option dominance, compact flow/subtour equivalent, feasible-column connectivity/elementarity, trip/multi-trip route resources, nonrestrictive slot bound, normalizers and sole objective | Manuscript equations (1)--(11), route/fleet-space definitions and their scope qualifiers | Uncalibrated generator mixing coefficients are not scientific model parameters; route-local arc variables are not route-master variables; option filtering requires the stated componentwise substitution proof |
| E15 | B — executable exact-component predicates | `exact/bpc/pricing/harvest.py`; `exact/bpc/pricing/completion_bounds.py`; `native/lunar_spprc/src/native_pricer.cpp`; `exact/solver/branch_probe.py`; proof-debt and node-bound modules | Addability-aware harvest, exact/context-guarded pruning, Ryan--Foster fractionality, debt blocking and bound fathoming | Manuscript equations (14)--(18) and (22)--(23) | A context-limited or diagnostic predicate must not be generalized into unrestricted proof authority |
| E16 | B — overall exactness proof chain | `CODEX_lunar_gat_bpc_exact_algorithm_design.md`; `exact/master/journey_rmp.py`; `exact/bpc/solver/branch_tree_solver.py`; `exact/core/branching.py`; `exact/core/cuts.py`; Native SPPRC exhaustive-status fields; proof-debt and node-bound modules | Canonical-route completeness assumptions, route-master equivalence, full node-LP closure, valid cuts, exact child partition, guidance invariance, tree gates and fail-closed states | Manuscript Lemmas 1--5, Theorem 1 and equations (24)--(27) | Proves soundness only for a returned tree-level exact conclusion within the fixed logical-path solution space; it does not prove unconditional completion or continuous-surface optimality |
| E17 | A/B — benchmark scenario and executable generator | `README.md`, real-map workflow paragraphs at lines 147--155; `src/lunar_ice_bpc/domain/scenario.py`; `src/lunar_ice_bpc/domain/real_maps.py`; `src/lunar_ice_bpc/domain/real_instance.py`; `paper_rewriting_output/lunar_scene_claim_map.md` | Common 50 km by 50 km real-map region, task-density scaling, configured higher-mobility scenario, candidate-site classes, task modes and three path options | Lunar-scene statements in Abstract and Sections 1--5 | The extent and speed are benchmark assumptions rather than current rover capability; resource/risk proxies are not in-situ abundance; no exclusive-PSR or territorial framing |

## Controlling Fact Boundaries

1. **Paper algorithm baseline.** The P0V2 experimental mainline is HiGHS
   restricted master + Native exact SPPRC pricing + Ryan–Foster branching +
   root-only P0 SRI-3. The no-cut line remains an experimental comparator and
   historical production-policy fact, not the paper's cut-family definition.
2. **Live SRI scope.** The manuscript contains only root-node SRI-3 under P0.
   Active-cut Phase-I, lineage, dual/context binding and exact cut-state support
   apply to admitted root cuts; descendants may inherit them but perform no new
   SRI separation.
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
   a reporting metric rather than another objective term. This exact
   three-term objective is mandatory throughout the abstract, body, equations,
   figures, tables, results, appendices, and Chinese translation. Legacy
   alpha/beta/gamma/delta fields remain internal compatibility data and must
   not enter manuscript-facing text.
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
10. **Drafting boundary.** `manuscript_draft.md` is the active Phase 4 English
    working manuscript. `section_3_pre_phase4_scratch.md` is the archived,
    non-authoritative consistency-check artifact. Missing learning results stay
    empty under `phase_4_placeholder_ledger.md`.
11. **Lunar-scene boundary.** The common `50 km × 50 km` map and configured
    rover mobility define a forward-looking benchmark scenario, not current
    hardware performance. Permanently shadowed regions are important candidate
    cold-trap environments but are not presented as the exclusive location of
    lunar water. Chang'E-5 sample studies support heterogeneous host materials
    and formation/retention factors, but their quantities are not transferred
    to south-pole candidate sites. Science-weighted completion remains an
    objective term rather than a territorial, ownership-priority, competition,
    or newly named urgency narrative.

## Research Routing

| Research Need | Primary Local Anchor | External Supplement Needed |
|---|---|---|
| Lunar south-pole water-ice exploration motivation and mission-epoch environment | E11, E12, E17; C061--C063 in the citation bank | Mission/science sources, recent lunar rover planning papers, and Q1 polar-shadow evidence; keep remote/sample evidence separate from site-level abundance, distinguish epoch-anchor spacing from routing horizon, and keep window-aggregated instances separate from departure-time-dependent routing |
| Multi-trip route formulation | E08, E10, E17 | Multi-trip/multi-graph VRP and energy-aware routing literature |
| Exact branch-price-and-cut architecture | E06, E07 | Recent BPC/column-generation papers and foundational pricing references |
| Learning-guided exact optimization | E08, E10 | Learning-to-price and learning-to-branch literature with exactness-preserving integration |
| Deterministic subset-row inequalities in live pricing | E06, E09 | SRI/cut-aware pricing literature; background only, never a learned-control contribution |
| Exactness and reproducibility | E01–E05 | Recent computational OR reporting and reproducibility norms |
| Target-journal rhetoric and structure | none | Six relevant TRC exemplars plus current official author guidance |
