# Phase 4 Overall Exactness Proof Audit

## Verdict

**PASS — CONDITIONAL OVERALL EXACTNESS PROOF WITH FAIL-CLOSED BOUNDARY**

The revised Section 4.7 proves that a closed and fully audited
branch-price-and-cut tree establishes global optimality of its best
exactly feasible incumbent over the fixed logical-path solution space.
Learning-order preservation is a supporting lemma rather than the main
theorem. The proof does not claim that the current implementation must finish
every instance.

## Proof-Obligation Review

| Obligation | Mathematical check | Implementation/evidence anchor | Verdict |
|---|---|---|---|
| Canonical route completeness | Same-endpoint path dominance admits a componentwise no-worse substitution with unchanged task/cut/branch coefficients; earlier service cannot worsen an upper time window, time-independent resource, or nonnegative completion term; induction covers visits and trip boundaries | Section 3.1 dominance rule; Eqs. (3), (6a)–(10); exact route construction; Native option filter | PASS under the stated assumptions |
| Route and fleet-schedule spaces | \(\mathcal R(\mathcal I)\) contains one-rover routes, \(\Omega(\mathcal I)\) contains exact-cover fleet schedules, and \(\mathcal P(n)\subseteq\mathcal R(\mathcal I)\) is the node route set | Sections 3.1 and 3.3; Lemma 2 | PASS; route and fleet objects no longer share one symbol |
| Trip-slot completeness | Every active trip contains at least one task and route-level task uniqueness permits at most \(|\mathcal T|\) active trips | Eq. (4a); \(\bar S=|\mathcal T|\) | PASS without an unstated truncation |
| Route-master equivalence | Exact task cover maps tasks to one selected route; fleet limit supplies one rover per route; valid SRI-3 rows preserve every integer schedule | Eq. (12); SRI-3 derivation after (20) | PASS |
| Full node-LP closure | Exact completion makes the RMP dual feasible for every full-master column; strong duality and restricted-column inclusion give both inequality directions in (25) | Eq. (13), Eq. (19), RMP/pricing RC audit | PASS in exact arithmetic |
| Phase-I infeasibility | A positive full Phase-I optimum after exhaustive Phase-I pricing excludes every zero-artificial LP solution and therefore every integer solution | `journey_rmp.py`; Phase-I proof contract | PASS |
| Cut preservation | Divisor-two SRI-3 follows from exact task coverage and the floor inequality | Eq. (20); `core/cuts.py` | PASS |
| Branch preservation | Exact cover makes same-route and different-route mutually exclusive and exhaustive; child filters implement those cases | Eq. (26); `core/branching.py` | PASS for an exact-valid pair |
| No-pair boundary | No Ryan–Foster pair is not integrality; absent a proved alternative disjunction, the node remains incomplete | `branch_tree_solver.py`; `NO_FRACTIONAL_RF_PAIR` contract | PASS; unconditional completion is not claimed |
| Learning preservation | Accepted hints permute unchanged work and candidates; exact completion and resolution of every deferred-pricing obligation prevent permanent loss | Eq. (23); Algorithm 2; proof-debt implementation queue | PASS under the typed-interface contract |
| Tree-level optimality | Integral, infeasible, bound-pruned, and branched nodes exhaust the closed tree; feasible incumbent plus valid lower bounds gives (27) | Eq. (14); tree gates and certificate ledger | PASS |
| Numerical scope | Formal equality uses exact arithmetic and zero comparison tolerances; executable status is tolerance-qualified | Section 4.7 and Appendix A | PASS with explicit qualification |

## Adversarial Cases

| Reviewer challenge | Resolution in the revised text |
|---|---|
| Time-dependent illumination or recharge can make delay useful | Lemma 1 excludes that model and requires a new pricing state/proof if introduced |
| A restricted-master objective is not automatically a node lower bound | Lemma 3 requires exhaustive true-dual pricing and proves full-dual feasibility |
| A learned or local pricing miss could be mistaken for closure | Only exhaustive exact completion may prove that no negative-reduced-cost route exists |
| A valid cut might be absent from pricing reduced cost | Lemma 3 requires one audited Eq. (13) under the full active cut context |
| A fractional LP with no Ryan–Foster pair could be declared integral | The node is explicitly incomplete unless another exact disjunction or aggregation proof exists |
| Learning could silently discard a negative column | Finite delay, explicit deferred-pricing obligations, release, and exhaustive repricing are theorem conditions |
| A delayed item could be absent from the proof-debt set before its reduced cost is known | Every delayed item is registered immediately with \(\bar c_d=\bot\) and remains recorded until true-dual recheck, exact processing, or context-matched exhaustive coverage |
| Native path-option filtering could omit a negative route | Same-endpoint componentwise dominance preserves task/cut/branch coefficients and gives a retained route with no greater objective or reduced cost |
| A resource limit could leak an optimality conclusion | Any open or unresolved node precludes a tree-level optimality conclusion |
| Floating-point tolerances could be confused with exact arithmetic | Mathematical and executable scopes are separated explicitly |
| Fixed-graph optimality could be generalized to continuous terrain | Theorem 1 and Appendix A retain the fixed logical-path qualifier |

## Automated Checks

- 21 targeted exactness-interface tests: PASS.
- `git diff --check`: PASS.
- 29 equation tags, all unique: PASS.
- Display, `aligned`, and `cases` environments balanced: PASS.
- Eight Markdown tables have consistent column counts: PASS.
- Heading hierarchy: PASS.
- First person, `sortie/journey`, SRI-5, `:=`, indicator notation, and
  unnecessary equivalence arrows in the manuscript: absent.
- Literal implementation enums, Boolean record fields, and configuration
  values used as algorithmic conclusions in the manuscript: absent.

## Five-Dimension Self-Review

| Dimension | Question | Assessment |
|---|---|---|
| Contribution | Does Section 4.7 prove the complete algorithm rather than only the learning interface? | PASS — learning preservation is Lemma 5; Theorem 1 covers the full BPC chain |
| Writing clarity | Can each proof obligation be located and followed independently? | PASS — one mathematical message per lemma, followed by a separate tree proof and scope qualification |
| Experimental strength | Does the theorem depend on missing learning-performance evidence? | PASS — no; empirical learning effects remain `TBD` and are not proof premises |
| Evaluation completeness | Are theorem conditions testable in future L0/L1/L2 runs? | PASS — the audit fields include pricing coverage, RC/context checks, debt, open/incomplete nodes, and ledger validity |
| Method soundness | Is any known implementation gap hidden by the word “exact”? | PASS WITH BOUNDARY — the missing no-pair alternative branch is stated and forces an incomplete outcome |

## Remaining Boundary

The current Ryan–Foster implementation is sound but not unconditionally
complete because it has no implemented alternative disjunction when a
fractional node supplies no Ryan–Foster pair. This is not a proof defect after
the revision: such a node remains unresolved, and Theorem 1 applies only to a
closed, fully audited tree. A future claim of unconditional algorithmic
completeness requires an implemented and proved representative or variable
fallback.
