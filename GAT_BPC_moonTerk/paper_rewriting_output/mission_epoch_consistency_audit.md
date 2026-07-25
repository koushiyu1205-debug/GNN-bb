# Mission-Epoch Consistency Audit

## Status

- Audit date: 2026-07-24
- Scope: complete English working manuscript and active PaperSpine evidence,
  notation, blueprint, rationale and placeholder artifacts
- Result: **PASS WITH M006 EVIDENCE STILL REQUIRED**

## Temporal Design Contract

The paper now separates three temporal quantities:

| Quantity | Planned value or source | Role |
|---|---|---|
| Environmental sample interval \(\Delta^{\mathrm{env}}\) | 1 h, adapted from C063 | Resolution used only in preprocessing |
| Epoch-anchor spacing | A southern-vernal-equinox reference followed by 12 anchors uniformly distributed over the 346.6-Earth-day draconic year, about 28.9 Earth days apart | Samples different environmental conditions |
| Seasonal phase group | South-polar spring, summer, autumn and winter, with three consecutive anchors per phase | Supports family-level paired comparison of completion measures |
| Mission horizon \(H^{\mathrm{mis}}\) | 960, 960, 1680, 1680, 3000 and 4560 min for task scales 5, 10, 20, 30, 50 and 100 | Limits route execution inside one instance |

The corresponding mission horizons are 16, 16, 28, 28, 50 and 76 h. The
near-lunation epoch spacing is not a route duration. Kloos et al. (C063)
supports hourly environmental modeling, 12-lunation coverage and substantial
polar-shadow variation. Wei et al. (C064) supports season-conditioned
illumination analysis for south-pole landing, power and traverse design.
Neither source establishes the four equal phase groups, a routing-horizon
duration, or a fastest phase.

For epoch \(\zeta\), anchor \(b_\zeta\) locates the mission window
\(\mathcal W_\zeta=[b_\zeta,b_\zeta+H^{\mathrm{mis}}]\). Hourly environmental
states over this window are converted by a declared preprocessing rule into
one fixed path-option instance \(\mathcal I^\zeta\). The aggregation rule is
outside BPC and must be frozen by M006. A conservative rule is preferable for
attributes that enter feasibility constraints; a representative rule may be
reported as a separate sensitivity case, but it must not be presented as a
physical safety guarantee.

## Full-Manuscript Check

| Manuscript unit | Check | Status |
|---|---|---|
| Abstract | Does not claim completed multi-epoch experiments or departure-time-dependent routing | PASS |
| Introduction | Uses a six-paragraph funnel and states only the fixed-instance seasonal-comparison boundary | PASS |
| Related work | Treats time-dependent routing as adjacent literature and leaves continuous environmental routing outside the current scope | PASS |
| Section 3 opening | Defines one fixed planning instance rather than one universally valid lunar environment | PASS |
| Section 3.1 | Defines \(\mathcal Q\), \(b_\zeta\), \(\mathcal W_\zeta\), \(\Delta^{\mathrm{env}}\), fixed per-instance attributes and omitted epoch superscripts | PASS |
| Section 3.2 | Uses fixed path attributes in time, energy, shadow and risk constraints; no departure-time switching remains | PASS |
| Section 3.3 | Keeps one normalized objective and common cross-epoch normalizers | PASS |
| Sections 4.1--4.6 | Learning and exact components act only on the frozen instance; no environmental state enters GAT authority, cuts or proof | PASS |
| Section 4.7 | Exactness theorem remains conditional on time-independent attributes within one window-aggregated instance | PASS |
| Section 5 | Records manifest horizons, four three-anchor phases, hourly preprocessing, paired controls and family-level phase analysis | PASS |
| Section 6 | Leaves phase results empty until M006 and requires phase/anchor/window/aggregation metadata, exact status and paired contrasts | PASS |
| Section 7 | Separates per-instance exactness from environmental fidelity, cross-epoch robustness and future rolling replanning | PASS |
| Conclusion | Does not promote the missing multi-epoch experiment into a contribution or result | PASS |
| Appendix A | States why preprocessing preserves the current proof and why within-route time dependence would require a new SPPRC and proof | PASS |
| Reference map | C063 is used for full-cycle temporal structure and C064 for season-conditioned operational relevance; neither supports the four-group definition, routing-horizon adequacy, phase ranking or algorithmic exactness | PASS |

## Evidence Boundaries

1. The current 120-instance corpus is single-environment evidence. The existing
   source catalog does not constitute the required 12-epoch hourly package.
2. Exact closure at scales 5--30 shows that their present horizons admit the
   reported benchmark optima under the current environment. It does not prove
   feasibility at every future epoch.
3. Scale-50 and scale-100 runs remain legally incomplete. Their 50 h and 76 h
   horizons must not be described as exactly validated task-completion
   durations.
4. M006 must provide the southern-vernal-equinox reference, epoch anchors,
   four phase labels, hourly illumination provenance, mission windows,
   aggregation rule, within-window variation, paired task/path records, common
   normalizers, exact/infeasible/incomplete outcomes, family-level phase
   summaries, paired contrasts and uncertainty.
5. If a path changes feasibility within a mission window, the point record
   must not be treated as fixed without qualification. The window must be
   shortened, split for rolling replanning, or converted to a declared
   conservative fixed instance before the existing exact solver is applied.

## Verdict

The manuscript follows the independent fixed-instance interpretation
throughout and organizes the 12 anchors into four south-polar phases without
changing the model or algorithm. The remaining limitation is empirical rather
than logical: M006 has not supplied the hourly environmental windows or paired
phase results. No phase ranking should be activated before that package
exists.
