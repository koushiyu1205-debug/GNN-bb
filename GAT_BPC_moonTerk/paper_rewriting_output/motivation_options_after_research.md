# Motivation Options After Research

All options preserve the user-selected mainline: **learning-guided exact
Branch-Price-and-Cut for lunar water-ice exploration vehicle routing**. They
differ in the breadth of the learned action space and therefore in the evidence
required. None assumes a performance result that has not yet been supplied.

| Option | One-Sentence Motivation | Core Innovation | Why It Is Not Overbroad | Required Evidence | Best-Fit Paper Arc |
|---|---|---|---|---|---|
| **A — Proof-preserving learning guidance across exact BPC (rejected)** | Exact multi-sortie fleet planning with explicit proofs for lunar water-ice prospecting is computationally demanding, motivating a learning-guided exact BPC architecture in which learned policies prioritize pricing, branching, and cut-management actions while the exact SPPRC/BPC path remains solely responsible for bounds, pruning, termination, and optimality proofs. | A lunar-structure-aware guidance layer plus an enforceable action contract, mandatory exact fallback, and proof/equivalence audit spanning the principal BPC control points. | It does not claim the first learning-guided exact BPC; You et al. (2026) is acknowledged as a direct branching precedent and Abouelrous et al. (2025) as a pricing precedent. Exactness is limited to the fixed logical-path solution space, and benefit remains unclaimed until experiments are supplied. | Implemented learned policy and training provenance; leakage-safe train/validation/test split; exact no-guidance BPC control; component ablations for pricing/branching/cuts; paired runtime, node, pricing, cut, and closure results; inference overhead and fallback frequency; proof/hash equivalence; held-out map/scale and OOD tests; failure-case audit. | Rejected because learned cut management is outside the confirmed scope and the multi-component burden is unnecessarily broad. |
| **B+ — Pricing-led guidance with secondary learned branching and mandatory exact completion (selected)** | The dominant search burden in lunar journey routing with explicit exact proofs motivates learning to prioritize pricing states, resources, or candidate columns and to rank a limited set of branching candidates, followed by mandatory native exact SPPRC completion and exact branch-validity/completeness fallbacks whenever a proof-bearing decision is required. | A problem-specific learned pricing scheduler as the primary mechanism, plus a secondary branch-candidate ranker; cut generation and management remain entirely deterministic. | Learning changes work order and candidate ranking only. Every official lower bound and pricing-completion statement is reproduced by native exact SPPRC, and branch validity and completeness are enforced by exact rules. The option claims neither a new general learning-to-price/branch paradigm nor any speedup before paired evidence exists. | Exact pricing-completion and branch-validity audits; proof that fallbacks execute before proof production; pricing hit/fallback rates; branch-ranker agreement, fallback frequency and node effects; no-guidance, pricing-only, and pricing-plus-branching controls; pricing-state expansions, time, memory, end-to-end paired results, inference overhead, held-out scales/maps, and comparison with hand-crafted baselines. No learned-cut ablation is permitted. | Lunar resource-constrained journeys → native exact SPPRC bottleneck → learned pricing prioritization → secondary branch ranking → exact completion and branch fallback contracts → component and end-to-end evaluation → operational scale boundary. |
| **C — Learning-guided live-SRI control inside exact BPC (rejected)** | Because valid subset-row inequalities can strengthen the master problem yet increase exact pricing-state cost, learning is motivated to decide when live SRI cuts should be activated, retained, or deferred under an exact do-no-harm and proof-preserving shell. | A learned cut-lifecycle policy coupled to exact SRI validity, Phase-I handling, lineage/context binding, exact cut-state pricing, and rollback/fallback gates. | The innovation is not SRI validity or learning-to-cut in general. It is the lunar BPC-specific control and safety interface; the frozen P0 result is reported honestly as correctness-passing but performance-failing, so a positive contribution requires new learning experiments rather than reinterpretation of existing diagnostics. | Trained cut policy and features; exact validity and lineage audits; no-cut, static/live-SRI, and learned-policy controls; activation/removal ablations; pricing-state and RMP effects; paired closure/time statistics with confidence intervals; rollback frequency; scale-30 analysis; demonstration that every final proof is unchanged by the policy. | Rejected because the confirmed scope explicitly prohibits learned cut control. |

## Cross-Dossier Synthesis

- **Scene Analyst:** every option treats the rover fleet as a transportation
  and logistics system and returns results to efficiency, reliability, safety,
  and resource use; a technology-only or aerospace-navigation story is avoided.
- **Exemplar Learner:** every option follows the target-journal pattern of
  problem structure → route-based model → tailored exact method → controlled
  experiments → operational interpretation.
- **SOTA Mapper:** every option accepts that learning-guided exact search,
  learned exact-BPC branching, learned routing pricing, and learning-to-cut have
  precedents. The candidate gap is therefore the lunar formulation and the
  implemented proof-preserving interface, subject to empirical
  validation.

## User Selection

The user selected **Option B**, modified to **B+**: pricing guidance is the
primary learned contribution, a limited learned branch-candidate ranking
component is included, and learned cut control is explicitly excluded. Option
A was rejected as too broad because it included learned cut management. Option
C was rejected because it made learned live-SRI control the contribution.

No option authorizes a claim that learning improves runtime, bounds, solve rate,
memory, robustness, or generalization until the corresponding frozen evidence
is available.
