# BPC_future Refactor Plan From Open-Source Review

Timestamp: 2026-06-08 23:20 CST

This plan targets the current exact BPC hard cases, especially root-tail
true-dual pricing where the final judge repeatedly finds only a small number of
negative columns. It intentionally avoids broad solver rewrites and parameter
chasing.

## Current Constraints

- Keep the 5-task and 10-task current best behavior frozen while optimizing
  20-task performance.
- Do not change the RMP mathematical model, cut coefficients, or branch
  semantics as part of this harvesting step.
- Do not let profile, streaming, zero-reference, GNN, or local no-column paths
  produce official lower bounds.
- Only `CERTIFIED_NO_NEGATIVE` from the true-dual direct-label /
  completion-bound final judge can close a node.

## Priority 1: Pricing State Semantics

Required explicit states:

- `FOUND_NEGATIVE`: at least one true-RC negative column was found.
- `FOUND_NEGATIVE_HARVESTED`: an expensive judge returned a batch of true-RC
  negative columns.
- `LOCAL_NO_COLUMN_UNCERTIFIED`: a worker did not find a column in its local
  configured universe.
- `CERTIFIED_NO_NEGATIVE`: official true-dual exact proof of no negative
  journey.
- `INCOMPLETE_TIME_LIMIT`: pricing stopped because of time budget.
- `INCOMPLETE_LABEL_LIMIT`: pricing stopped because of sequence/label budget.
- `DUPLICATE_ONLY`: generated negative candidates were already forbidden or
  duplicate and cannot advance the RMP.

Acceptance rule: only `CERTIFIED_NO_NEGATIVE` may update official node lower
bound or prove optimality.

## Priority 2: Hidden-Negative Audit

When a worker returns local no-column and the judge later finds a negative
journey, log enough data to explain the miss:

- hidden journey signature, task set, and mask;
- true reduced cost and reduced-cost components;
- duplicate / forbidden-signature filter result;
- task-set bound, resource pruning, dominance, profile catalog, and branch
  filter involvement where available;
- ordinary worker status, reason, exhausted flag, and configured universe.

Goal: repair worker coverage and diagnostics. This is not a certificate path.

## Priority 3: Support-Aware Pareto Harvesting

Implemented first as the minimal closed loop in this change.

Behavior:

- Candidate journeys are filtered by `manual_journey_reduced_cost` under the
  true RMP duals and active cuts.
- Only `true_rc < -eps` and non-forbidden signatures can be returned.
- Selection ranks by exact reduced cost, then uses task-set diversity,
  Jaccard/containment thresholds, active-support distance, and replacement cap.
- New task masks and active-support-changing masks are preferred over weak
  replacement-only columns.
- Fallback fill may return additional true-RC negative columns when diversity
  alone cannot fill the configured batch.

Diagnostics:

- `candidate_negative_count`
- `selected_count`
- `selected_new_mask_count`
- `selected_support_changing_count`
- `selected_strong_replacement_count`
- `selected_weak_replacement_count`
- `rejected_overlap_count`
- `fallback_fill_count`
- `best_true_rc`
- `worst_selected_true_rc`
- `avg_pairwise_jaccard`

Correctness rule: harvesting is a return-selection policy only. Empty harvest
does not certify no negative column; partial harvest remains a found-negative
state, not `CERTIFIED_NO_NEGATIVE`.

## Priority 4: Final Judge Trigger Gating

The final judge should be delayed until it is likely to pay for itself:

- root node or root-tail phase;
- certificate candidate;
- ordinary/profile/streaming worker returned `LOCAL_NO_COLUMN_UNCERTIFIED`;
- objective is flat or dual movement indicates tail degeneracy;
- remaining time is sufficient for the heavy judge budget.

Avoid using completion-bound / direct-label final judge as an early discovery
worker.

## Priority 5: Profile / Streaming Workers

Profile and streaming pricing should be treated as batch column workers:

- they may find and return negative columns;
- they may seed profile catalogs from judge-found hidden negatives;
- their no-column result is `LOCAL_NO_COLUMN_UNCERTIFIED` unless they exhaust
  the full configured journey universe under true-dual exact semantics.

Worker logs should expose local universe size, reason, and exhausted status.

## Priority 6: Tail Dual Center / Stabilization

Tail dual-center methods may reduce degeneracy and candidate churn, but they
must stay outside the official proof path:

- candidate pricing can use smoothed, previous, zero-reference, or learned
  task-cover anchors;
- official final judge uses true RMP duals, or a dual proven by the LP solver
  to be certificate-equivalent;
- GNN anchors cannot contribute to lower-bound certificates.

Root-tail zero-reference should remain a gated breaker for root-tail phases,
not a default branch-heavy subtree setting.

## Immediate Implementation Slice

This change lands only the Priority 3 slice:

- add `BPC_future/pricing/journey_harvesting.py`;
- expose `harvest_support_aware_negative_journeys(...)`;
- make `journey_pricing.py` use the new selector through a compatibility alias;
- add focused unit tests in `BPC_future/tests/test_journey_harvesting.py`;
- preserve existing config names, existing direct-label diagnostics, and all
  certificate semantics.

## Verification

Minimum verification for this slice:

- run `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python -m unittest BPC_future.tests.test_journey_harvesting`;
- run targeted existing diverse-harvest tests from
  `BPC_future/tests/test_bpc_future.py`;
- run pricing state / certificate unit tests that assert local no-column does
  not become `CERTIFIED_NO_NEGATIVE`;
- run one 5-task smoke after tests pass.

Do not launch full 5/10/20 benchmark sweeps as part of this small refactor.
