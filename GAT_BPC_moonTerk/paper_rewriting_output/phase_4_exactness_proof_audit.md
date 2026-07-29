# Phase 4 Overall Exactness Proof Audit

## Verdict

**PASS FOR THE FROZEN NO-TASK-WAIT IMPLEMENTATION — CONDITIONAL EXACTNESS
SCOPE RETAINED**

The revised Section 4.7 conditionally proves that a closed and fully audited
branch-price-and-cut tree establishes global optimality of its best
exactly feasible incumbent over the fixed logical-path solution space.
Learning-order preservation is a supporting lemma rather than the main
theorem. The frozen revised executable implements common depot-departure
adjustment and arrival-equals-service-start timing, passes compact/native
timing tests, and binds its guarded dominance and exhaustive-coverage context.
The theorem remains conditional on every row passing its full proof gates.

## Proof-Obligation Review

| Obligation | Mathematical check | Implementation/evidence anchor | Verdict |
|---|---|---|---|
| Canonical route completeness | Equal-travel-time path substitution preserves all task times; any reduced recharge duration is absorbed as depot waiting so later departures can remain fixed; every fixed task/path trip yields the departure interval in (3); choosing its lower endpoint is feasible and weakly improves nonnegative weighted completion; induction covers trip boundaries because earlier depot availability can be followed by depot waiting | Section 3.1; Eqs. (3), (6a)–(10); Lemma 1; EV035--EV036 | PASS AS MATHEMATICAL AND IMPLEMENTED CONTRACT |
| Route and fleet-schedule spaces | \(\mathcal R(\mathcal I)\) contains one-rover routes, \(\Omega(\mathcal I)\) contains exact-cover fleet schedules, and \(\mathcal P(n)\subseteq\mathcal R(\mathcal I)\) is the node route set | Sections 3.1 and 3.3; Lemma 2 | PASS; route and fleet objects no longer share one symbol |
| Trip-slot completeness | Every active trip contains at least one task and route-level task uniqueness permits at most \(|\mathcal T|\) active trips | Eq. (4a); \(\bar S=|\mathcal T|\) | PASS without an unstated truncation |
| Route-master equivalence | Exact task cover maps tasks to one selected route; fleet limit supplies one rover per route; valid SRI-3 rows preserve every integer schedule | Eq. (12); SRI-3 derivation after (20) | PASS |
| Full node-LP closure | Exact completion makes the RMP dual feasible for every full-master column only if no-wait timing and guarded dominance preserve a no-worse continuation. Eq. (17) allows depot subset dominance only for a nonempty visited set, equal cut state, and continuation-preserving branch compatibility; active-trip dominance is disabled. Eq. (18) relies on the nonnegative input domain and positive normalizers, permits branch restrictions that only shrink the continuation set, and is disabled whenever an active cut could add an omitted cut-dual term; strong duality and restricted-column inclusion then give both inequality directions in (25) | Eqs. (13), (16)–(19); Lemma 3; EV035--EV036 | PASS WITH THE DISPLAYED GUARDS |
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
| Path-option filtering could omit a slower route needed to avoid early arrival | Options with unequal travel time are retained; substitution is allowed only at equal travel time with all remaining attributes weakly no worse |
| Earlier open-trip labels could incorrectly dominate later ones | Active-trip dominance is disabled because a later release can force a retroactive common departure shift |
| The initial empty depot label could dominate every completed depot label | Eq. (17) requires the dominating visited set to be nonempty |
| A branch-incompatible subset label could remove a needed continuation | Depot subset dominance requires the continuation-preserving branch predicate and equal active-cut state |
| Zero future increments in the completion bound could be invalid under negative inputs | Section 3.1 declares all task/path cost and resource inputs nonnegative, and Eq. (9) makes every normalizer strictly positive; the implementation gate includes an input-domain audit |
| Approximate travel-time equality could delete a timing-distinct path | Mathematical substitution requires equality; proof-bearing native completion uses the frozen \(10^{-12}\) comparison, whereas the Python seed/reference path uses \(10^{-9}\) and has no no-negative proof authority |
| A resource limit could leak an optimality conclusion | Any open or unresolved node precludes a tree-level optimality conclusion |
| Floating-point tolerances could be confused with exact arithmetic | Mathematical and executable scopes are separated explicitly |
| Fixed-graph optimality could be generalized to continuous terrain | Theorem 1 and Appendix A retain the fixed logical-path qualifier |

## Automated Checks

The revised manuscript passed the syntax, notation, and equation-environment
checks. Three targeted Python tests, two native tests, and the frozen-package
verification passed for the no-task-wait implementation. The new independent
manuscript reviews are recorded in `structured_review.md`.

## Five-Dimension Self-Review

| Dimension | Question | Assessment |
|---|---|---|
| Contribution | Does Section 4.7 prove the complete algorithm rather than only the learning interface? | PASS — learning preservation is Lemma 5; Theorem 1 covers the full BPC chain |
| Writing clarity | Can each proof obligation be located and followed independently? | PASS — one mathematical message per lemma, followed by a separate tree proof and scope qualification |
| Experimental strength | Does the theorem depend on missing learning-performance evidence? | PASS — no; empirical learning effects remain `TBD` and are not proof premises |
| Evaluation completeness | Are theorem conditions testable in future L0/L1/L2 runs? | PASS — the revised L0 control binds timing, dominance, instance, engine and proof fields; L1/L2 must use the same schema |
| Method soundness | Is any known implementation gap hidden by the word “exact”? | PASS WITH BOUNDARY — the missing no-pair alternative branch remains explicit and fail closed |

## Remaining Boundary

The no-task-wait implementation boundary is closed for the frozen scale-5--30
control. Revised-model cut-effect, state-refinement, and scale-50/100 evidence
still requires new runs. The remaining algorithmic boundary is Ryan–Foster
completeness. The
current Ryan–Foster implementation is sound but not unconditionally
complete because it has no implemented alternative disjunction when a
fractional node supplies no Ryan–Foster pair. This is not a proof defect after
the revision: such a node remains unresolved, and Theorem 1 applies only to a
closed, fully audited tree. A future claim of unconditional algorithmic
completeness requires an implemented and proved representative or variable
fallback.
