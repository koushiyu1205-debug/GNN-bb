# BPC Future Optimization Failure Notes

This document records optimization paths that looked plausible but did not
improve the current exact-safe mainline.  Revisit them only with new evidence.

## 2026-06-08: Zero-Reference Stabilized Dual Is Promising But Not A 10-Task Breakthrough

Context:

- Hard 10-task roots were dominated by degenerate true-dual tails: completion-bound
  final judge returned inactive replacement columns, RMP re-solved on a flat
  objective face, then another true-dual final judge exposed the next small
  replacement batch.
- Existing official stabilized-dual support was exact-safe only after current
  pool dual feasibility and dual-objective checks, but its `l1_reference` mode
  followed the previous/SCIP dual by default.  A new opt-in
  `journey_dual_stabilization_reference_mode=zero` lets the same L1 selector
  minimize distance to the zero vector instead, while preserving the same
  official feasibility checks before certificate pricing may use the dual.

Change:

- Added `journey_dual_stabilization_reference_mode` in
  `_select_journey_pricing_duals` with allowed modes:
  `previous`/`previous_pricing`/`last`, `scip`/`current`/`true`, and
  `zero`/`none`/`origin`.
- Default behavior remains `previous`: use the previous pricing dual when
  available, otherwise SCIP's current dual.
- The log now records both `reference` (effective reference) and
  `reference_mode` (requested mode).  Zero-reference results still enter
  exact/certificate pricing only as `stabilized_certificate` after objective
  match and current-pool nonnegative reduced-cost validation.

Probe evidence:

- `tranq10_01` zero-reference probe:
  `BPC_future/results/probe_zero_ref_dual_stab_tranq10_01_20260608.csv`.
  Result: exact `OPTIMAL`, `75.852985s`, primal/dual `202.698698`,
  `12` RMP solves, `22` pricing calls, `10` exact calls, `473` columns.
  This fixes the previous `240s` timeout / `253s` profile run.  The only
  completion-bound retry was a final
  `stabilized_certificate / CERTIFIED_NO_NEGATIVE` at `cg_iter=12`.
- `tranq10_09` zero-reference probe:
  `BPC_future/results/probe_zero_ref_dual_stab_tranq10_09_20260608.csv`.
  Result: exact `OPTIMAL`, `162.861692s`, primal/dual `203.102839`,
  `18` RMP solves, `44` pricing calls, `26` exact calls, `493` columns.
  This improves the current safe baseline around `193.24s`, but final judge
  still had three negative replacement retries before the certificate.
- `tranq10_04` zero-reference probe:
  `BPC_future/results/probe_zero_ref_dual_stab_tranq10_04_20260608.csv`.
  Result: exact `OPTIMAL`, `181.821925s`, primal/dual `207.893439`,
  `16` RMP solves, `39` pricing calls, `23` exact calls, `463` columns.
  This improves the current full-run timing around `232.27s`, but still needs
  three completion-bound negative retries before final proof.

Full-suite A/B evidence:

- Full 10-task zero-reference run:
  `BPC_future/results/all_tasks10_zero_ref_dual_stab_20260608.csv`.
  Command used the normal 10-task config with opt-in
  `journey_dual_stabilization_reference_mode=zero`, learning still enabled,
  and a `240s` per-instance engineering limit.
- Result: `20/20` exact `OPTIMAL`, total solve time `1353.69s`, max
  `212.28s`, `8/20` above `60s`, `3/20` above `120s`, `2/20` above `200s`.
  All finish records had `open_nodes=0` and `pricing_incomplete_nodes=0`.
- Compared with `BPC_future/results/full_tasks10_20260608.csv`, zero-reference
  improved total finite runtime by about `301.16s` and converted
  `tranq10_01` from `TIME_LIMIT` at `238.13s` to exact `OPTIMAL` at
  `118.85s`.
- The gains were concentrated on Tranquillitatis root-tail cases:
  `tranq10_02` `44.54s -> 15.13s`, `tranq10_05` `108.48s -> 39.16s`,
  `tranq10_07` `136.59s -> 70.86s`, and `tranq10_10` `70.51s -> 43.31s`.
- Apollo branch-heavy cases regressed under the same opt-in:
  `apollo10_04` `163.90s -> 212.28s` and `15 -> 19` nodes;
  `apollo10_07` `54.51s -> 95.69s` and `9 -> 17` nodes.  This is the
  decisive reason not to promote zero-reference globally.
- Certificate audit found no worker-local false certificate.  Every
  `global_certificate=True` pricing record was
  `CERTIFIED_NO_NEGATIVE / direct_label_no_negative_journey` with source
  `scip_certificate` or `stabilized_certificate`.  Branch leaves can also close
  through `DUPLICATE_ONLY` followed by
  `journey_duplicate_only_certificate_audit exact_safe=true`; one Apollo leaf
  had a negative reduced-cost column only at its upper bound, which is exact-safe
  for fathoming but is not treated as a global no-negative certificate.

Diagnosis:

- The effect is real on sampled Tranquillitatis root-tail hard cases: zero
  reference reduces degenerate dual ping-pong enough to remove the `tranq10_01`
  timeout and cut roughly 20-30% from `tranq10_04`/`tranq10_09`.
- It does not solve the 10-task target.  `tranq10_01` remains above `60s`, and
  `tranq10_04`/`tranq10_09` remain far above `60s`; full-suite A/B also shows
  Apollo branch-heavy regressions.
- Completion-bound additions in these probes are still mostly inactive
  replacement columns.  Zero-reference changes the dual face enough to shorten
  the tail, but it does not create broad active-support or new-task-set impact.

Decision:

- Keep the opt-in code and test.  It is exact-safe by construction and is the
  first tail-dual probe in this round with a clear positive signal.
- Do not enable it in the main 5/10/20 configs.  The full 10-task A/B shows
  useful Tranquillitatis root-tail gains, but Apollo branch-heavy regressions
  are too large for a global default.
- If revisited, gate it narrowly to root-tail certificate candidates after
  branch risk is ruled out, and compare against Apollo10_04/Apollo10_07 before
  promoting.
- If promoted after A/B, keep the certificate logs audited for
  `pricing_dual_source=stabilized_certificate`, `pricing_state=CERTIFIED_NO_NEGATIVE`,
  and `current_pool_negative_reduced_cost_count=0`.

Implementation follow-up:

- Added opt-in `journey_dual_stabilization_reference_mode=root_tail_zero`.
  Unlike global `zero`, this mode attempts zero-reference stabilization only
  when the selector is at a root-tail certificate candidate.  By default it
  requires `depth <= 0`, `certificate_candidate=True`, and
  `certificate_flat_rounds >= 0`; otherwise it logs
  `reason=root_tail_zero_gate` and returns the SCIP dual without solving the
  stabilized-dual LP.  This keeps branch nodes on the baseline dual path.
- Two-instance probe:
  `BPC_future/results/probe_root_tail_zero_gate_apollo10_07_tranq10_09_20260608.csv`.
  `apollo10_07` returned to baseline behavior: exact `OPTIMAL` in `53.672909s`,
  `9` nodes, root branch `RF(2,10)`, and `0` accepted stabilized duals.
  The global-zero run had taken `95.691864s` and `17` nodes.
- The same gated run preserved the root-tail benefit on `tranq10_09`: exact
  `OPTIMAL` in `161.774780s`, `1` node, `13` accepted stabilized duals, all at
  `depth=0` with `reference=zero`, and final certificate
  `stabilized_certificate / CERTIFIED_NO_NEGATIVE /
  direct_label_no_negative_journey`.
- Full 10-task gated run:
  `BPC_future/results/all_tasks10_root_tail_zero_gate_20260608.csv`.
  Result: `20/20` exact `OPTIMAL`, total solve time `1227.015s`, max
  `180.381s`, `7/20` above `60s`, `3/20` above `120s`, `0/20` above `200s`.
  This improves both the full baseline (`1654.859s`, one `TIME_LIMIT`) and
  global zero-reference (`1353.694s`, max `212.277s`).
- Apollo branch-heavy behavior is preserved: Apollo total time `444.260s` vs
  baseline `451.084s` and global zero `536.910s`; Apollo total nodes `52`,
  matching baseline and avoiding global zero's `64` nodes.  Key hard cases:
  `apollo10_04` `161.277s / 15 nodes` vs baseline `163.896s / 15 nodes` and
  global zero `212.277s / 19 nodes`; `apollo10_07` `53.603s / 9 nodes` vs
  baseline `54.509s / 9 nodes` and global zero `95.692s / 17 nodes`.
- Tranquillitatis root-tail benefit is preserved: Tranq total time `782.755s`
  vs baseline `1203.775s` and global zero `816.784s`.  `tranq10_01` becomes
  exact `OPTIMAL` in `108.670s` instead of the baseline `238.130s`
  `TIME_LIMIT`; `tranq10_04` improves to `180.381s`, and `tranq10_09` to
  `163.085s`.
- Full-suite gate audit found no bad stabilized-dual acceptance and no false
  global certificate.  Every accepted stabilized dual had
  `reference=zero`, `reference_mode=root_tail_zero`, `depth=0`,
  `objective_matches=True`, `current_pool_dual_feasible=True`, and
  `current_pool_negative_reduced_cost_count=0`.  Every global certificate was
  `CERTIFIED_NO_NEGATIVE / direct_label_no_negative_journey` with source
  `scip_certificate` or `stabilized_certificate`.
- This gate is now a strong candidate for the 10-task mainline, but it should
  still be checked on the 5-task full suite for no regression and on selected
  20-task hard probes before being promoted to default.

## 2026-06-07: Relaxed 5/10 Runs Show Exactness Is Mostly Restored, But 10-Task Tail Proof Is Still Too Expensive

Context:

- After enabling direct-label cross-count dominance in the mainline configs,
  the full 5-task and 10-task suites were rerun with exact-safe certificate
  semantics: profile/streaming no-column is local and uncertified; official
  node convergence still requires true-dual direct-label / completion-bound
  final judge.
- The 10-task target time of `60s` is a performance target, not a hard
  correctness cutoff.  A `240s` full-suite run was used to expose where the
  exact proof is slow instead of prematurely stopping every hard tail.

Evidence:

- 5-task full suite:
  `BPC_future/results/all_tasks05_cross_count_current_20260607.csv`.
  All `20/20` instances are exact `OPTIMAL`; average `0.920s`, median
  `0.947s`, max `1.925s`.
- 10-task full suite with `240s` limit:
  `BPC_future/results/all_tasks10_cross_count_current_240s_20260607.csv`.
  `19/20` instances are exact `OPTIMAL`; one instance,
  `tranquillitatis_balmer_like_20km_tasks10_01_seed11000`, hit `TIME_LIMIT`.
  Among exact instances, average `80.336s`, median `58.068s`, max
  `228.295s`.
- The remaining timeout was rerun alone with `900s`:
  `BPC_future/results/probe_tranq10_01_cross_count_long900_20260607.csv`.
  It reached exact root `OPTIMAL` in `290.014s`, primal/dual `202.698698`,
  gap `0.0`, `1` node, `19` RMP solves, `48` pricing calls, `29` exact
  pricing calls, `10.58M` generated sequences, `446` columns.

Diagnosis:

- The slow 10-task cases split into two different families.
- Branch-tree hard case:
  `apollo15_20km_tasks10_04_seed11055` is exact `OPTIMAL` at `228.30s` but
  uses `19` branch nodes, `35` RMP solves, `110` pricing calls, and `75`
  exact pricing calls.  Its bottleneck is repeated true-dual certificate work
  across branch nodes, not a single root tail.
- Root-tail hard cases:
  `tranq10_01`, `tranq10_04`, `tranq10_07`, `tranq10_09`, and `tranq10_06`
  are all root-only or root-dominated.  Profile/heuristic pricing works early,
  then fails in the tail with `partial_profile_scan_no_negative_journey` while
  exact streaming/direct-label keeps finding true-RC negative columns.
- The worst pattern is not simply "cannot find columns": the final judge often
  spends about a minute, returns only a few weak negative columns, and the RMP
  objective remains flat.  This repeats until the last heavy no-negative
  certificate finally closes the root node.
- Therefore the main unsolved issue is the degenerate tail proof loop:
  true-dual final judge becomes an expensive column worker, and the returned
  columns are too weak or too redundant to move the RMP basis quickly.

Current decision:

- Keep cross-count dominance enabled: it is exact-safe and gives a small,
  repeatable search reduction.
- Do not treat the 2026-06-07 performance as a global regression.  Compared
  with the earlier `120s` runs, the current line certifies many instances that
  previously timed out.  The higher average is partly because hard cases are
  now allowed to run to proof.
- The next performance work should target root-tail degeneracy and final-judge
  productivity, not early profile scanning.  The most relevant next probes are:
  stronger true-RC negative-column harvesting from the final judge, active-rate
  logging for returned columns, and a proof-safe way to avoid repeated
  `negative_journeys_already_in_pool` / weak-negative cycles.

## 2026-06-07: Direct-Label Cross-Count Dominance Is A Small Safe Win, Not The Tail Breakthrough

Context:

- After the dominance-aware harvest run, the remaining hard-tail bottleneck on
  `tranq10_09` was still two expensive true-dual completion-bound final-judge
  calls.  The existing direct-label cross-count dominance rule was exact-safe
  but disabled by default in the mainline configs.
- The rule only compares labels with the same visited-task mask.  A label using
  fewer sorties and no worse end time / reduced-cost value dominates a label
  using more sorties because it leaves at least as much remaining sortie
  capacity for future extensions.

Probe:

- Command:
  `/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_10_journey.yaml --set journey_pricing_direct_journey_label_cross_count_dominance_enabled=True --instances BPC_future/data/generated/moon_trek_60/logical_graphs/tranquillitatis_balmer_like_20km/tasks_10/tranquillitatis_balmer_like_20km_tasks10_09_seed11144_logical_graph.json --time-limit 600 --results-csv BPC_future/results/probe_direct_cross_count_tranq10_09_long600_20260607.csv --log-dir BPC_future/results/logs/probe_direct_cross_count_tranq10_09_long600_20260607 --solution-dir BPC_future/results/solutions/probe_direct_cross_count_tranq10_09_long600_20260607`.

Outcome:

- Result remained exact root `OPTIMAL`: primal `203.102839`, dual
  `203.102839`, gap `0.0`, `1` node, `492` columns.
- Wall-clock improved from the dominance-aware baseline `235.26s` to
  `223.18s`.
- Total generated sequences fell from about `7.85M` to about `7.17M`.
- `direct_label_cross_count_pruned_labels` was `9970` across the run.
- In the two heavy completion-bound calls:
  - `cg_iter=20`: generated sequences dropped from `2.97M` to `2.63M`;
    `direct_label_cross_count_pruned_labels=5307`.
  - `cg_iter=21`: generated sequences dropped from `2.92M` to `2.58M`;
    `direct_label_cross_count_pruned_labels=4663`.

Decision:

- Enable `journey_pricing_direct_journey_label_cross_count_dominance_enabled`
  in the 5/10/20 mainline configs.  It is exact-safe and gives a repeatable
  small reduction in final-judge search.
- Do not over-credit it.  The last two completion-bound calls still generate
  millions of labels, so the dominant unresolved issue is still the true-dual
  certificate DP, not duplicate harvest or ordinary worker behavior.

Follow-up: 15x15 completion-bound buckets are worse.

- Probe:
  `/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_10_journey.yaml --set journey_certificate_completion_bound_time_buckets=15 --set journey_certificate_completion_bound_energy_buckets=15 --instances BPC_future/data/generated/moon_trek_60/logical_graphs/tranquillitatis_balmer_like_20km/tasks_10/tranquillitatis_balmer_like_20km_tasks10_09_seed11144_logical_graph.json --time-limit 600 --results-csv BPC_future/results/probe_cb_15x15_cross_count_tranq10_09_long600_20260607.csv --log-dir BPC_future/results/logs/probe_cb_15x15_cross_count_tranq10_09_long600_20260607 --solution-dir BPC_future/results/solutions/probe_cb_15x15_cross_count_tranq10_09_long600_20260607`.
- Result remained exact `OPTIMAL`, primal/dual `203.102839`, but wall-clock
  worsened to `284.61s`.
- CB calls increased from `3` to `4`, total generated sequences rose from
  about `7.17M` to about `9.47M`, and `two_cycle_state_count` rose from
  `83853` to `177408`.
- The finer table found additional tail negative replacements instead of
  shortening the proof.  Keep the current `10x10` completion-bound buckets for
  this mainline.

## 2026-06-07: Task-Set-Dominance-Aware Harvest Removes Duplicate Batches But Does Not Shorten The Certificate Enough

Context:

- The relaxed `tranq10_09` run showed that mask closure was incompatible with
  the current `JourneyPool` task-set dominance semantics: the pool keeps only
  one representative per task set, so multiple physical alternatives for the
  same mask mostly become unchanged replacements after the expensive final
  judge has already found them.

Implementation:

- `_select_diverse_journey_candidates` now accepts
  `dominant_task_set_costs`.
- When task-set dominance is active, the selector collapses candidates by task
  set before harvest selection and keeps only the raw-cost-best candidate for
  each task set.  This mirrors `JourneyPool.add`, where raw cost is the
  dominance criterion for identical master-column coefficients.
- Mask closure is automatically disabled in this mode because same-mask
  multi-column closure cannot survive the pool's one-representative-per-task-set
  rule.
- Added a regression test:
  `test_harvest_respects_task_set_dominance_before_mask_closure`.

Validation:

- Compile:
  `PYTHONDONTWRITEBYTECODE=1 /home/kai/miniconda3/bin/python -m compileall -q BPC_future/pricing/journey_pricing.py BPC_future/solver/journey_driver.py BPC_future/tests/test_bpc_future.py`.
- Unit tests:
  `python -m unittest BPC_future.tests.test_bpc_future -k harvest -v` and
  `python -m unittest BPC_future.tests.test_bpc_future.BPCFutureTests.test_certificate_completion_bound_is_tail_and_root_only -v`.
- 5-task smoke:
  `BPC_future/results/probe_dominance_aware_harvest_smoke_tasks05_20260607.csv`
  solved `apollo15_20km_tasks05_01_seed6000` exactly in about `1.95s`.

Hard-tail probe:

- Result file:
  `BPC_future/results/probe_dominance_aware_harvest_tranq10_09_long600_20260607.csv`.
- Instance:
  `tranquillitatis_balmer_like_20km_tasks10_09_seed11144`.
- Outcome remained exact root `OPTIMAL`: primal `203.102839`, dual
  `203.102839`, gap `0.0`, `1` node.
- Wall-clock was `235.26s`, only slightly better than the previous relaxed
  mask-closure run (`238.64s`).
- Final column count dropped from `514` to `492`, showing the duplicate/unchanged
  batch issue was real and mostly removed.
- Completion-bound retries dropped from `5` calls to `3` calls, but total CB
  time stayed high: about `157.9s`.
- CB additions became clean:
  - `cg_iter=12`: requested `10`, added `10`, duplicate/unchanged `0`.
  - `cg_iter=20`: requested `9`, added `9`, duplicate/unchanged `0`.
- The last two heavy CB calls still dominated:
  - `cg_iter=20`: about `76.1s`, found `9` negative replacements after
    generating about `2.97M` sequences.
  - `cg_iter=21`: about `74.3s`, certified no negative after generating about
    `2.92M` sequences.

Decision:

- Keep the dominance-aware harvest.  It aligns final-judge output with what
  the master can actually accept and reduces column bloat.
- Do not expect it to solve hard tails by itself.  After duplicate batches are
  removed, the bottleneck is clearly the expensive true-dual final-judge search
  on the degenerate tail.
- Next proof-side work should target the certificate DP itself: stronger
  completion-bound pruning, cheaper exact no-negative certification, or a
  tail dual center that reduces the number of near-identical replacement probes
  before the final judge is invoked.

## 2026-06-07: Long Tranq10-09 Run Proves Exactness But Exposes Final-Judge And Duplicate-Replacement Bottlenecks

Context:

- `tranq10_09` was rerun with the current support-aware harvest and mask
  closure mainline under a relaxed `600s` time limit to get the real optimality
  certificate instead of stopping at the former `120s` target.
- Command:
  `/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_10_journey.yaml --instances BPC_future/data/generated/moon_trek_60/logical_graphs/tranquillitatis_balmer_like_20km/tasks_10/tranquillitatis_balmer_like_20km_tasks10_09_seed11144_logical_graph.json --time-limit 600 --results-csv BPC_future/results/probe_mask_closure_tranq10_09_long600_20260607.csv --log-dir BPC_future/results/logs/probe_mask_closure_tranq10_09_long600_20260607 --solution-dir BPC_future/results/solutions/probe_mask_closure_tranq10_09_long600_20260607`.

Outcome:

- Status is true root `OPTIMAL`: primal `203.102839`, dual `203.102839`,
  gap `0.0`, `1` node, `24` RMP solves, `66` pricing calls,
  `42` exact pricing calls, `514` final columns.
- Wall-clock was `238.64s`.  The old `120s` runs failed because the instance
  still needed another final-judge negative-column loop plus a full
  no-negative certificate after the target time.
- The objective reached `203.102839` by `cg_iter=9` and stayed exactly flat
  through `cg_iter=24`.  The active support hash also stayed unchanged in all
  logged tail diagnostics.  This is a degenerate replacement tail, not a
  primal incumbent discovery problem.

Timing breakdown:

- `exact_completion_bound_retry`: `5` calls, about `148.6s` total.  This is
  the dominant cost.
- Regular `exact`: `23` calls, about `73.9s` total.
- `heuristic`: `24` calls, only about `2.8s` total.
- `exact_retry`: `3` calls, about `4.4s` total.
- `same_dual_supplement`: `6` calls, about `3.6s` total.

Completion-bound detail:

- `cg_iter=14`: CB took `6.98s`, found `12` selected negatives; only `4`
  were added and `8` were duplicate-filtered.
- `cg_iter=16`: CB took `10.88s`, found `15` selected negatives; only `5`
  were added and `10` were duplicate-filtered.
- `cg_iter=22`: CB took `11.65s`, found `14` selected negatives; only `3`
  were added and `11` were duplicate-filtered.
- `cg_iter=23`: CB took `36.16s`, found `11` selected negatives; only `5`
  were added and `6` were duplicate-filtered.
- `cg_iter=24`: CB took `82.92s` and finally returned
  `CERTIFIED_NO_NEGATIVE` / `direct_label_no_negative_journey`.  This single
  proof generated `3,298,327` sequences and `3,807,263` LB-pruned labels;
  bound build time was only about `1.63s`, so the bottleneck is the forward
  final-judge search, not bound construction.

Diagnosis:

- The certificate chain is now semantically correct: ordinary/profile
  `no_negative_journey` is only local/uncertified.  In this same run, ordinary
  exact reported local no-column at `cg_iter=14` and `16`, but CB then found
  hidden negative columns.  Only the final CB `CERTIFIED_NO_NEGATIVE` at
  `cg_iter=24` proved convergence.
- Support-aware harvest and mask closure help expose the failure mode, but the
  selected CB candidates are still mostly replacement columns under existing
  masks/task sets.  They do not change the LP objective or active support.
- The harvest selector is currently allowed to count candidates before the
  master duplicate/signature filter.  In the long run, CB selected `52`
  negative candidates across four negative retries, but only `17` were added.
  The remaining `35` were filtered as duplicates after the expensive judge
  work had already been paid for.
- Learning remained enabled, but it was not the tail bottleneck in this run:
  it contributed early true-RC-kept columns, then alpha decayed to `0.05` and
  most tail rounds produced no strong true-RC candidates, forcing true-dual
  exact pricing.

Next useful changes:

- Make final-judge harvest addability-aware before selection: remove or
  heavily deprioritize candidates whose journey signature already exists in
  the master/forbidden set before counting them toward `min_fill` or
  `max_returned_journeys`.
- Treat replacement harvest as a bounded fallback.  Prefer genuinely addable
  new signatures and support-changing masks; do not spend the whole CB batch
  budget on duplicates that will be discarded by `add_journeys`.
- Improve the final no-negative certificate search itself.  The last proof
  still costs `82.9s` after two-cycle and resource completion bounds, so the
  next proof-side work should target stronger pruning or a cheaper exact
  certificate path rather than more early worker heuristics.

## 2026-06-07: Mask Closure Helps Batch Replacements But Still Does Not Close Tranq10-09

Context:

- Support-aware harvest showed that the `tranq10_09` completion-bound final
  judge candidate universe had no new/support-changing task-set directions.
  The next hypothesis was that repeated replacement alternatives under the
  same active/repeated task masks should be closed in the same expensive judge
  call instead of reappearing one by one in later rounds.

Implementation:

- `JourneyPricingConfig` now exposes
  `direct_journey_label_mask_closure_enabled`,
  `direct_journey_label_mask_closure_max_masks`, and
  `direct_journey_label_mask_closure_max_columns_per_mask`.
- Final-judge diverse harvest can now bypass the one-column-per-task-set rule
  only for bounded active/repeated replacement masks.  All selected columns
  still come from true-RC negative direct-label/completion-bound candidates.
- The 5/10/20 mainline configs enable mask closure with max `8` masks and max
  `6` columns per mask.  The global `max_returned_journeys` cap still limits
  the total returned batch size.
- Logs now include:
  `harvest_mask_closure_candidate_task_set_count`,
  `harvest_mask_closure_selected_count`, and
  `harvest_mask_closure_selected_task_set_count`.

Validation:

- Compile:
  `PYTHONDONTWRITEBYTECODE=1 /home/kai/miniconda3/bin/python -m compileall -q BPC_future/pricing/journey_pricing.py BPC_future/solver/journey_driver.py BPC_future/tests/test_bpc_future.py`.
- Unit tests:
  `python -m unittest BPC_future.tests.test_bpc_future -k mask_closure -v`,
  `python -m unittest BPC_future.tests.test_bpc_future -k diverse_journey_harvest -v`,
  `python -m unittest BPC_future.tests.test_bpc_future -k support_aware -v`, and
  `python -m unittest BPC_future.tests.test_bpc_future.BPCFutureTests.test_certificate_completion_bound_is_tail_and_root_only -v`.
- 5-task smoke:
  `BPC_future/results/probe_mask_closure_smoke_tasks05_20260607.csv`
  solved `apollo15_20km_tasks05_01_seed6000` exactly in about `2.02s`.

Hard-tail probe:

- Result file:
  `BPC_future/results/probe_mask_closure_tranq10_09_20260607.csv`.
- Instance:
  `tranquillitatis_balmer_like_20km_tasks10_09_seed11144`.
- Outcome stayed root `TIME_LIMIT`, primal `203.102839`, no dual bound, about
  `114.47s`, with `485` columns.  This is faster than the immediately previous
  support-aware-only probe (`119.20s`, `477` columns) but still not exact.
- Completion-bound retries showed mask closure did fire:
  - `cg_iter=12`: `candidate_negative_count=38`, selected `20`,
    `new_cand=0`, `support_cand=0`, closure selected `15` columns across
    `3` masks.
  - `cg_iter=17`: `candidate_negative_count=28`, selected `14`,
    `new_cand=0`, `support_cand=0`, closure selected `9` columns across
    `3` masks.
- The final incomplete reason was `weak_negative_journeys_filtered`, not a
  completed no-negative certificate.

Decision:

- Keep mask closure infrastructure and counters.  It does exactly what it is
  supposed to do: batch repeated replacement alternatives from the same masks.
- Do not treat it as a complete `tranq10_09` solution.  It reduced some tail
  cost but did not create new/support-changing directions or close the global
  certificate.
- The remaining replacement-tail issue is now sharper: after batching repeated
  replacements, the tail still ends with weak true-RC negatives and no final
  certificate.  The next useful work is likely a stronger no-candidate/weak-tail
  proof bound or a policy for weak-negative certificate handoff, not more
  replacement harvesting.

## 2026-06-07: Support-Aware Harvest Is Implemented, But Tranq10-09 Has No Support-Changing Candidates

Context:

- The final-judge diverse harvest selector was upgraded to a support-aware
  bucket order: new task-set directions, low-overlap active-support changes,
  strong replacements, and then capped weak replacements.
- The exactness boundary is unchanged.  The selector only ranks true-RC
  negative journeys already found by the true-dual direct-label /
  completion-bound judge.

Implementation:

- `JourneyPricingConfig` now exposes
  `direct_journey_label_diverse_harvest_support_aware_enabled`,
  `direct_journey_label_diverse_harvest_support_overlap_threshold`,
  `direct_journey_label_diverse_harvest_replacement_cap`, and
  `direct_journey_label_diverse_harvest_strong_replacement_threshold`.
- The 5/10/20 mainline configs enable support-aware harvest with
  support overlap `0.6`, weak replacement cap `8`, and strong replacement
  threshold `-1e-4`.
- Logs now include support-aware counters:
  `harvest_candidate_support_changing_count`,
  `harvest_selected_support_changing_count`,
  `harvest_selected_strong_replacement_count`, and
  `harvest_selected_weak_replacement_count`.

Validation:

- Compile:
  `PYTHONDONTWRITEBYTECODE=1 /home/kai/miniconda3/bin/python -m compileall -q BPC_future/pricing/journey_pricing.py BPC_future/solver/journey_driver.py BPC_future/tests/test_bpc_future.py`.
- Unit tests:
  `python -m unittest BPC_future.tests.test_bpc_future -k diverse_journey_harvest -v`,
  `python -m unittest BPC_future.tests.test_bpc_future -k support_aware -v`, and
  `python -m unittest BPC_future.tests.test_bpc_future.BPCFutureTests.test_certificate_completion_bound_is_tail_and_root_only -v`.
- 5-task smoke:
  `BPC_future/results/probe_support_aware_harvest_smoke_tasks05_20260607.csv`
  solved `apollo15_20km_tasks05_01_seed6000` exactly in about `1.98s` with
  `CERTIFIED_NO_NEGATIVE/global_certificate=true`.

Hard-tail probe:

- Result file:
  `BPC_future/results/probe_support_aware_harvest_tranq10_09_20260607.csv`.
- Instance:
  `tranquillitatis_balmer_like_20km_tasks10_09_seed11144`.
- Outcome stayed root `TIME_LIMIT`, primal `203.102839`, no dual bound, about
  `119.20s`, with `477` columns.
- The two completion-bound retries showed the selector was active but had no
  support-changing material:
  - `cg_iter=11`: `candidate_negative_count=141`, selected `10`, `new_cand=0`,
    `support_cand=0`, all `10` selected were strong replacements.
  - `cg_iter=12`: `candidate_negative_count=201`, selected `8`, `new_cand=0`,
    `support_cand=0`, all `8` selected were strong replacements.

Decision:

- Keep the support-aware harvest infrastructure and counters.  It is
  exact-safe and makes the real failure mode visible.
- Do not expect support-aware ordering alone to break the current
  `tranq10_09` replacement tail.  The final judge candidate universe contained
  no new/support-changing task-set directions in the tested rounds.
- The next replacement-tail step should be mask closure or another mechanism
  that deliberately exhausts repeated replacement alternatives for the same
  active masks, rather than only reordering distinct task sets.

## 2026-06-07: Dynamic SRC Separation Does Not Hit The Current Tranq10-09 Tail

Context:

- Static SRC budget sweeps had already failed to recover the old fast
  `tranq10_09` path, but dynamic SRC activation timing had not been checked
  against the current exact-safe mainline.
- The hypothesis was that the root tail might become fractional in a way that
  static lexicographic SRC missed, and that dynamically separated subset-row
  cuts could reduce the replacement-only pricing tail without changing
  certificate semantics.  SRC coefficients depend only on task sets in journey
  mode, so this remains exact-safe with current task-set dominance.

Probes:

- `BPC_future/results/probe_dynamic_src_tranq10_09_20260607.csv`
  enabled dynamic SRC for the first three CG rounds on
  `tranquillitatis_balmer_like_20km_tasks10_09_seed11144`.
- `BPC_future/results/probe_dynamic_src_late_tranq10_09_20260607.csv`
  extended the same separator through CG round 25 with the same moderate
  budget:
  `journey_dynamic_subset_row_cut_budget=280`,
  `journey_dynamic_subset_row_max_added=25`, and
  `journey_dynamic_subset_row_max_subset_size=6`.

Observed behavior:

- Both probes stayed root `TIME_LIMIT`, primal `203.102839`, no dual
  certificate, with the same `492` columns as the current baseline.
- The early probe ran three separation attempts; the late probe ran 21
  attempts.  Every attempt generated `281` candidate cuts and found
  `violated=0`, `added=0`.
- The final completion-bound retries remained replacement-only:
  the late probe's final CB selected `9` negative journeys with
  `harvest_selected_new_task_set_count=0` and
  `harvest_selected_replacement_task_set_count=9`.

Decision:

- Do not enable `journey_dynamic_subset_row_cuts_enabled` in the 5/10/20
  mainline configs from this evidence.  On the current hard root, the dynamic
  separator simply does not find violated cuts; extending its activation window
  only adds small overhead.
- Future cut work should improve cut candidate quality or add a different
  valid inequality family.  Do not continue changing dynamic SRC round/budget
  parameters blindly.

## 2026-06-07: Flat-Weak Column Pressure Still Does Not Break the Current Hard Tail

Context:

- The current 10-task audit still has root hard cases where the RMP objective
  is flat while exact/Profile/CB workers keep adding small batches of valid
  true-RC negative journeys.
- `journey_certificate_flat_weak_column_pressure_enabled` is designed to keep
  these weak additions from fully resetting certificate pressure.  That is
  exact-safe in principle because it only changes scheduling pressure; it does
  not turn worker no-column into a certificate.

Probe:

- `BPC_future/results/probe_flat_weak_pressure_tranq10_09_20260607.csv`
  tested `journey_certificate_flat_weak_column_pressure_enabled=True` on
  `tranquillitatis_balmer_like_20km_tasks10_09_seed11144`.
- `BPC_future/results/probe_flat_weak_pressure_tranq10_04_20260607.csv`
  tested the same switch on
  `tranquillitatis_balmer_like_20km_tasks10_04_seed11054`.

Observed behavior:

- `tranq10_09` stayed root `TIME_LIMIT`, primal `203.102839`, no dual bound,
  about `119.08s`, with `483` columns.  The switch correctly marked repeated
  flat additions as weak, but later CB retries still returned inactive
  replacement-heavy batches and did not close the root certificate.
- `tranq10_04` stayed root `TIME_LIMIT`, primal `207.893439`, no dual bound,
  about `119.25s`, with `487` columns.  The switch delayed useful final proof
  even further: the last CB retry started with only about `19s` remaining.

Decision:

- Do not enable `journey_certificate_flat_weak_column_pressure_enabled` by
  default.  It identifies the pathology, but under the current scheduler it
  encourages more late worker activity without producing a certificate.
- The hard root cases still need either a stronger final CB/direct-label proof
  or a worker that changes active support.  Weak-pressure scheduling alone is
  not enough.

## 2026-06-07: Resource-Coarsened Hidden Patrol Finds Replacement Columns But Still Misses the Tail

Context:

- The Level 2.5 hidden-negative patrol can be run without K-beam truncation by
  enabling resource coarsening and setting `max_labels_per_node=0`.
- This is a true-dual worker-only probe: columns are exact feasible columns and
  no-column results are ignored.  It never produces a certificate.

Probe:

- Result file:
  `BPC_future/results/probe_hidden_patrol_coarse02_tranq10_09_20260607.csv`.
- Instance:
  `tranquillitatis_balmer_like_20km_tasks10_09_seed11144`.
- Overrides:
  `journey_hidden_negative_patrol_resource_coarsening_enabled=True`,
  `journey_hidden_negative_patrol_max_labels_per_node=0`,
  `journey_hidden_negative_patrol_time_limit=0.2`,
  `journey_hidden_negative_patrol_min_journeys=2`, and
  `journey_hidden_negative_patrol_max_returned_journeys=8`.

Observed behavior:

- Outcome stayed root `TIME_LIMIT`, primal `203.102839`, no dual bound,
  about `119.19s`, with `486` columns.
- The patrol did find some hidden negatives earlier: for example `cg_iter=9`
  found `2` direct-label negative journeys, and an after-retry patrol at
  `cg_iter=14` found `2`.
- These additions still did not affect active support:
  the late patrol and CB additions logged `active_changed_task_set_count=0`,
  and the final CB remained necessary.  The last CB retry still returned a
  replacement-heavy batch and the run timed out.

Decision:

- Do not enable resource-coarsened hidden patrol by default.  It is exact-safe
  and can find additional columns, but on the current `tranq10_09` tail they
  are the same inactive/replacement type that has repeatedly failed to move
  the RMP.
- If revisited, the worker needs a filter or objective that explicitly targets
  active support / genuinely different task sets; simply widening Level 2.5 is
  not enough.

## 2026-06-07: Active-Priority Harvest Now Receives Active Sets, But Tranq10-09 Has No Active Candidates

Context:

- Completion-bound diverse harvesting supports `priority_task_sets`, but the
  root/branch final completion-bound retry calls were not consistently passing
  the current RMP active task sets into `price_journeys`.
- This meant active-priority harvest probes could report zero priority
  candidates without proving whether the final judge candidate set actually
  overlapped active support.

Implementation:

- `BPC_future/solver/journey_driver.py` now passes
  `priority_task_sets=active_task_sets` to final and escalation
  completion-bound `price_journeys` calls.
- With the default
  `journey_certificate_completion_bound_diverse_harvest_min_priority_task_sets=0`,
  this does not change selection behavior.  It only makes priority-candidate
  counters and explicit priority-quota probes meaningful.

Validation:

- Compile check:
  `PYTHONDONTWRITEBYTECODE=1 /home/kai/miniconda3/bin/python -m compileall -q BPC_future/solver/journey_driver.py`.
- 5-task smoke:
  `BPC_future/results/probe_priority_passthrough_smoke_tasks05_20260607.csv`
  solved `apollo15_20km_tasks05_01_seed6000` to exact `OPTIMAL`,
  primal=dual=`102.041475`, gap `0`, about `1.95s`.

Hard-case probe:

- Result file:
  `BPC_future/results/probe_cb_priority_active_tranq10_09_20260607.csv`.
- Instance:
  `tranquillitatis_balmer_like_20km_tasks10_09_seed11144`.
- Overrides:
  `journey_certificate_completion_bound_diverse_harvest_min_priority_task_sets=4`
  and
  `journey_certificate_completion_bound_diverse_harvest_priority_overlap_threshold=0.4`.
- Outcome stayed root `TIME_LIMIT`, primal `203.102839`, no dual bound,
  about `119.08s`, and columns `492`.
- The final completion-bound retries now had active sets available, but both
  logged `harvest_candidate_priority_task_set_count=0` and
  `harvest_selected_priority_task_set_count=0`.  Their selected columns stayed
  replacement-only and inactive.

Decision:

- Keep the priority-task-set passthrough fix because it corrects the final
  judge interface and makes future active-priority diagnostics real.
- Do not enable a positive active-priority harvest quota by default.  On the
  current `tranq10_09` replacement-tail, the expensive true-RC negative
  candidates simply do not overlap active support under the tested threshold.
  The tail needs different column directions or a stronger proof, not just a
  priority quota.

## 2026-06-07: Immediate Certificate No-Reserve Worsens Tranq10-04

Context:

- `tranq10_04` is a root no-candidate proof hard case in the current 10-task
  audit.  In the baseline rerun, the completion-bound final judge starts late,
  around `93.6s`, with only about `26.5s` remaining.
- It was plausible that `journey_certificate_immediate_no_reserve_enabled=True`
  could move more time into exact pricing once an incumbent-backed certificate
  candidate exists, without changing certificate semantics.

Probe:

- Result file:
  `BPC_future/results/probe_immediate_no_reserve_tranq10_04_20260607.csv`.
- Instance:
  `tranquillitatis_balmer_like_20km_tasks10_04_seed11054`.
- Override:
  `journey_certificate_immediate_no_reserve_enabled=True`.

Observed behavior:

- Outcome remained root `TIME_LIMIT`, primal `207.893439`, no dual bound,
  wall time about `118.23s`, and columns increased to `488` versus the rerun
  baseline's `446`.
- The switch triggered from `cg_iter=2` onward and expanded ordinary exact
  pricing windows very early.  This produced many true-dual negative columns
  but did not move active LP support enough to finish.
- The final completion-bound judge started even later than baseline, around
  `101.07s` with about `20.5s` remaining, and timed out with no negative
  candidate: `generated_sequences=179950`, `candidate_trips=88`,
  `best_reduced_cost=-0.0`, `pricing_state=INCOMPLETE_LIMIT`.

Decision:

- Do not enable `journey_certificate_immediate_no_reserve_enabled` by default.
  It spends proof budget on early ordinary exact worker behavior and worsens
  the final certificate window on this no-candidate hard root.
- The useful fix is not a broad no-reserve exact-pricing expansion.  For
  no-candidate roots, the scheduler needs a more precise final-judge handoff or
  a stronger completion-bound proof; for replacement-tail roots, it needs
  active-support/new-task-set progress, not more early ordinary exact columns.

## 2026-06-07: Soft-Return 4 / Wider Learning Keep / Branch Two-Cycle Off Did Not Fix Current 10-Task Hard Cases

Context:

- After the exact certificate audit rerun, 5-task solved `20/20` exactly under
  the `120s` engineering limit, while 10-task solved `15/20` exactly and left
  five hard cases at `TIME_LIMIT`.
- Three targeted probes were run against the current exact-safe mainline to
  test small proof-safe changes before touching defaults.

Probes:

- `BPC_future/results/probe_cb_soft4_tranq10_07_20260607.csv`
  tested earlier completion-bound diverse-harvest returns on
  `tranquillitatis_balmer_like_20km_tasks10_07_seed11108`:
  `journey_certificate_completion_bound_diverse_harvest_min_journeys=4`,
  `journey_certificate_completion_bound_diverse_harvest_min_fill=4`,
  `journey_certificate_completion_bound_diverse_harvest_soft_return_min_journeys=4`,
  and soft return after `6s`.
- `BPC_future/results/probe_learning_keep8_thresh1_tranq10_09_20260607.csv`
  tested wider learning true-RC retention on
  `tranquillitatis_balmer_like_20km_tasks10_09_seed11144`:
  `journey_learning_true_rc_keep_threshold=1.0` and
  `journey_learning_true_rc_max_kept_per_round=8`.
- `BPC_future/results/probe_branch_twocycle_off_apollo10_04_20260607.csv`
  tested disabling completion-bound two-cycle tables below the root on
  `apollo15_20km_tasks10_04_seed11055`:
  `journey_certificate_completion_bound_two_cycle_branch_enabled=False`.

Observed behavior:

- Soft-return `4` did not convert `tranq10_07`; it stayed root `TIME_LIMIT`
  at about `114.62s`, slightly worse than the rerun baseline.  The final
  completion-bound retry selected only `1` replacement negative column and did
  not trigger a useful early return.
- Wider learning retention kept `8` true-RC negative learning columns in the
  first round of `tranq10_09`, but the instance still timed out at about
  `119.10s`.  Later completion-bound batches remained replacement-only
  (`new_task_set_count=0`), so the extra early learning columns did not break
  the tail degeneracy.
- Disabling two-cycle tables in branch nodes did not improve `apollo10_04`;
  it still timed out at about `120.00s` with the same primal/dual gap and
  essentially the same column count.  The branch hard case is not primarily a
  two-cycle table overhead problem.

Decision:

- Do not lower the default completion-bound diverse-harvest soft-return
  threshold to `4`.
- Do not widen the default learning true-RC keep policy based on this probe.
  Learning is still enabled and useful as a worker, but the current hard tail is
  not fixed by simply keeping more early true-negative learning columns.
- Do not disable branch two-cycle completion bounds by default.  If branch proof
  is revisited, target branch oracle quality and incomplete-pricing recovery
  rather than this switch.

Follow-up, duplicate task-set harvesting:

- `BPC_future/results/probe_cb_allow_dup_tasksets_tranq10_09_20260607.csv`
  tested allowing completion-bound diverse harvest to return multiple physical
  columns with the same task set on `tranq10_09`.
- The run still timed out at about `119.09s`, with fewer columns than the
  baseline.  Completion-bound retries returned four batches of `16`
  replacement-only columns, but `harvest_selected_new_task_set_count` stayed
  `0` throughout.
- Decision: do not enable duplicate task-set harvesting by default.  The hard
  root is not solved by adding more replacement physical representatives under
  the same task-set universe; the remaining work needs either a stronger final
  proof or a worker that discovers genuinely different active/new task sets.

## 2026-06-07: Full 5/10 Rerun Shows Improvement, But Hard Cases Split Into Two Bottlenecks

Context:

- A fresh full rerun used the current exact-safe mainline after the pricing
  status-semantics fixes, duplicate-only audit promotion, completion-bound
  two-cycle table, learning anchor, and conservative same-dual supplement.
- Engineering time limits were `120s` for both 5-task and 10-task runs.

Result files:

- 5-task:
  `BPC_future/results/all_tasks05_current_20260607_rerun.csv`.
- 10-task:
  `BPC_future/results/all_tasks10_current_20260607_rerun.csv`.

Observed behavior:

- 5-task solved `20/20` exactly.  Average time was about `0.91s`, max about
  `1.88s`.
- 10-task solved `14/20` exactly and left `6/20` at `TIME_LIMIT`.  Average
  time was about `67.32s`; `9/20` instances still exceeded the final `60s`
  target.
- This is not a global regression versus
  `BPC_future/results/all_tasks10_current_20260605.csv`: the old snapshot had
  `13/20` exact, `7/20` time limits, and `13` instances over `60s`.  The
  current rerun improved most Apollo cases and moved
  `tranquillitatis_balmer_like_20km_tasks10_10_seed11162` from timeout to exact.

Current hard-case split:

- Root proof hard cases, especially Tranquillitatis roots, are dominated by
  ordinary true-dual profile/direct-label generation plus completion-bound
  final-judge search.  Example:
  `tranquillitatis_balmer_like_20km_tasks10_06_seed11090` reaches a local
  no-column state around `49.9s`, then the CB final judge spends about `68.1s`
  generating about `3.41M` direct-label sequences, prunes about `3.45M`
  labels by bounds, finds no candidate, and still times out without a global
  certificate.
- Degenerate replacement-tail hard cases, especially
  `tranquillitatis_balmer_like_20km_tasks10_09_seed11144`, repeatedly reach
  `objective_delta=0` while duals keep moving.  CB can find true-RC negative
  batches, but selected columns are mostly replacement task sets and do not
  change the active support enough to finish the root proof.
- Branch proof hard cases, especially `apollo15_20km_tasks10_04_seed11055`,
  do certify several branch nodes but still time out deeper in the tree with
  incomplete pricing.  This is a different bottleneck from the root-only
  Tranquillitatis cases.

Decision:

- Do not describe the current mainline as simply worse than the older June 5
  current run; the aggregate 10-task result improved.  The remaining issue is
  concentrated hard-case proof cost.
- Do not revisit already rejected broad knobs such as 15/15 CB buckets,
  suffix-only next-sortie caching, NG preprobe defaults, profile catalog
  seeding, or generic no-column same-dual unlock without new evidence.
- A pure global sequence cap on direct-label CB is not a solution: some exact
  10-task certificates currently need more than `1.5M` generated direct-label
  sequence events, so enforcing that cap globally would turn solved instances
  into incomplete runs.  If cap semantics are tightened later, it must be
  treated as budget protection, not a speed proof.
- The next useful direction should either strengthen the actual final proof
  for the no-candidate root cases, or generate active-support/new-task-set
  columns earlier for the degenerate replacement-tail cases.  More replacement
  workers alone are unlikely to solve the target.

Follow-up, unique-route exact first step:

- A default-on, exact-safe strengthening was added:
  `journey_certificate_completion_bound_unique_route_exact_first_step_enabled`.
  The UniqueRoute completion bound still uses the existing bucket DP for the
  recursive suffix, but the first return/task transition from a current
  direct-label prefix is evaluated using the prefix's real time and energy
  before falling back to buckets.  The pricing bound takes the max of the old
  bucketed value and this exact-first-step value, so it remains a valid lower
  bound.
- Full 5-task override probe:
  `BPC_future/results/probe_unique_route_exact_first_step_tasks05_20260607.csv`
  solved `20/20` exactly, average about `0.91s`, max about `1.88s`.
- Positive 10-task hard-root probe:
  `BPC_future/results/probe_unique_route_exact_first_step_tranq10_06_20260607.csv`.
  `tranquillitatis_balmer_like_20km_tasks10_06_seed11090` moved from root
  `TIME_LIMIT` to exact `OPTIMAL` in about `110.28s`, with a true-dual
  `CERTIFIED_NO_NEGATIVE` completion-bound final judge.
- Neutral/mixed 10-task probes:
  `probe_unique_route_exact_first_step_tranq10_09_20260607.csv` remained root
  `TIME_LIMIT` at about `119.07s`;
  `probe_unique_route_exact_first_step_remaining_hard10_20260607.csv` left
  `apollo10_04`, `tranq10_01`, `tranq10_04`, and `tranq10_07` as
  `TIME_LIMIT`, although `tranq10_07` improved to about `113.72s`.
- Decision: keep the exact-first-step UniqueRoute bound enabled in the main
  5/10/20 configs.  It improves at least one no-candidate proof hard root,
  is neutral on the sampled replacement-tail case, and is a no-op for 20-task
  UniqueRoute DP because that helper is disabled above its mask limit.  Do not
  treat it as the final 10-task solution; replacement-tail and branch-tail
  bottlenecks remain.

## 2026-06-07: Cross-Count Direct-Label Dominance Is Exact-Safe But Not A Hard-Root Win

Context:

- Direct journey-label pricing originally dominated labels only within the same
  sortie count.  For the same visited task mask, a label using fewer sorties,
  no later end time, and no larger value is an exact-safe dominator because it
  leaves at least as much remaining sortie capacity.  Cut coefficients in the
  current journey pricing universe depend on task masks and non-empty fleet
  participation, not the number of used sorties.
- A configurable cross-count dominance helper was added to support this pruning
  without changing any certificate semantics.  It records only the lightweight
  `direct_label_cross_count_pruned_labels` count.

Probe:

- Result file:
  `BPC_future/results/probe_cross_count_tranq10_06_20260607.csv`.
- Instance:
  `tranquillitatis_balmer_like_20km_tasks10_06_seed11090`.
- Compared against:
  `BPC_future/results/all_tasks10_current_20260607_060341.csv`.

Observed behavior:

- The hard root remained `TIME_LIMIT` with the same incumbent and column count.
- The final completion-bound judge did prune `23,293` cross-count labels, so
  the mechanism is active.
- Wall time was slightly worse: the representative final judge went from about
  `67.50s` to about `68.36s`; generated sequences also increased from about
  `1.51M` to about `1.70M`.  The pruning changed the search frontier but did
  not strengthen the certificate proof enough to reduce wall time.

Decision:

- Keep cross-count dominance as an opt-in diagnostic/experimental knob:
  `journey_pricing_direct_journey_label_cross_count_dominance_enabled`.
- Do not enable it by default in the 5/10/20 mainline configs.  It is
  exact-safe, but current evidence says it is not the hard Tranquillitatis root
  bottleneck fix.

## 2026-06-07: Global New-Task-Set Harvest Gate Helps One Tail But Hurts The Batch

Context:

- Hard Tranquillitatis roots often show replacement-only completion-bound
  harvesting.  A plausible exact-safe policy was to require the final judge's
  diverse harvest soft return to include at least one new task set before it
  returns a negative batch.  The intended effect was to stop the final judge
  from becoming a replacement-column worker.
- The tested overrides were:
  `journey_certificate_completion_bound_diverse_harvest_min_new_task_sets=1`
  and
  `journey_certificate_completion_bound_diverse_harvest_soft_return_min_new_task_sets=1`.

Probes:

- 5-task full probe:
  `BPC_future/results/probe_cb_min_new_taskset_tasks05_20260607.csv`.
  It solved `20/20` exactly, average about `0.93s`, max about `1.92s`.
- Tranquillitatis hard/near-hard probes:
  `probe_cb_min_new_taskset_tranq10_01_09_10_20260607.csv` and
  `probe_cb_min_new_taskset_tranq10_04_06_07_20260607.csv`.
  The gate improved `tranq10_10` substantially in the isolated probe
  (`102.46s -> 80.88s`) and slightly improved some timeout cases, but did not
  convert any remaining timeout into a certificate.
- Full 10-task default probe with the gate:
  `BPC_future/results/all_tasks10_cb_min_new_taskset_default_20260607.csv`.

Observed behavior:

- Full 10-task status stayed `15/20` exact and `5/20` time limits.
- Average runtime worsened from about `65.35s` to about `67.54s`.
- Instances over `60s` worsened from `8/20` to `10/20`.
- The gate strongly helped `tranq10_10` (`102.46s -> 81.47s`) but hurt several
  otherwise solved instances, especially `tranq10_05` (`50.04s -> 91.11s`) and
  `tranq10_02` (`43.12s -> 52.08s`).

Decision:

- Revert the global default.  Keep both min-new-task-set harvest gates at `0`
  in the 5/10/20 configs.
- If this idea is revisited, make it adaptive and state-driven: only after a
  root final judge has already returned replacement-only batches or after an
  objective-flat replacement tail is detected.  Do not apply it globally from
  the first final-judge call.

Follow-up, adaptive replacement-tail gate:

- A small opt-in implementation was attempted to turn on the min-new-task-set
  gate only after prior replacement-only completion-bound batches.  The first
  probe was stopped after the防回归 instance
  `tranquillitatis_balmer_like_20km_tasks10_05_seed11072` regressed from
  `OPTIMAL` in about `50.04s` to root `TIME_LIMIT` at about `118.13s`.
- Log inspection also showed the state wiring was not robust enough: the
  intended adaptive mode did not reliably appear in the retry mode payload, so
  the implementation was removed rather than kept as dormant complexity.
- Decision: do not keep an adaptive replacement-tail gate in the code until
  there is a simpler state model and a clear reason why it will not damage
  normal proof cases like `tranq10_05`.

## 2026-06-07: Pre-Expansion Suffix-Bound Pruning Worsened A Hard Root

Context:

- Direct-label completion-bound pruning already checks suffix lower bounds
  after a new sortie is appended and before a new journey label is inserted.
- A plausible exact-safe micro-optimization was to also check the same
  optimistic suffix bound immediately after popping an existing journey-prefix
  label, before generating its next-sortie candidates.  If the prefix could not
  possibly be completed into a negative journey, this would skip the expensive
  next-sortie generation step.

Probe:

- Result file:
  `BPC_future/results/probe_prefix_suffix_bound_tranq10_06_20260607.csv`.
- Instance:
  `tranquillitatis_balmer_like_20km_tasks10_06_seed11090`.
- The patch was exact-safe in semantics and passed focused direct-label /
  completion-bound unit tests.  A 5-task smoke stayed exact:
  `BPC_future/results/probe_prefix_suffix_bound_tasks5_20260607.csv`,
  `OPTIMAL`, primal=dual=`102.041475`, about `1.886s`.

Observed behavior:

- The hard root still timed out with the same incumbent and column count.
- The representative completion-bound final judge became slightly worse:
  baseline generated about `3.322M` next-sortie candidates and spent about
  `67.47s`; the pre-expansion suffix-bound patch generated about `3.508M`
  candidates and spent about `68.33s`.
- Bound pruning counts rose, but the altered priority/frontier order caused
  more overall search before timeout.  More local pruning did not translate
  into lower wall-clock time or a certificate.

Decision:

- The patch was reverted.  Do not reintroduce pre-expansion suffix-bound
  pruning as a default optimization without a broader profiler-backed reason.
- This is another example where an exact-safe local pruning rule can still
  worsen the best-first direct-label frontier on hard degenerate roots.

## 2026-06-07: Current NG Preprobe Executes But Does Not Close The Hard Root

Context:

- Older 2026-06-04 notes showed NG/DSSR tail probes helping some 10-task
  runs under the then-current certificate chain, but a later flag-only probe
  accidentally did not exercise NG (`ng_dssr_iterations=0`).
- A fresh current-mainline probe explicitly enabled NG as a bounded preprobe
  while keeping it worker-only unless it can produce a proper relaxed
  certificate.

Probe:

- Result file:
  `BPC_future/results/probe_ng_preprobe_current_tranq10_09_20260607.csv`.
- Instance:
  `tranquillitatis_balmer_like_20km_tasks10_09_seed11144`.
- Overrides included:
  `journey_pricing_direct_journey_label_ng_dssr_enabled=True`,
  `journey_pricing_direct_journey_label_ng_exact_probe_enabled=True`,
  `journey_pricing_direct_journey_label_ng_min_cg_iter=7`,
  `journey_pricing_direct_journey_label_ng_disable_below_remaining=8.0`,
  `journey_pricing_direct_journey_label_ng_probe_time_limit=0.4`, and
  `journey_pricing_direct_journey_label_ng_max_labels=50000`.

Observed behavior:

- Outcome stayed root `TIME_LIMIT`: primal `203.102839`, no dual bound,
  `columns=500`.
- Unlike the earlier flag-only probe, NG really executed: `51` pricing rows
  had NG statistics.  Aggregate exact rows logged `ng_dssr_iterations=29`,
  `ng_label_pops=11549`, and `ng_generated_labels=47110`; same-dual supplement
  rows added another `21` NG iterations.
- The extra worker activity did not reduce the proof tail.  Exact pricing calls
  grew, profile-DP time increased substantially, and the run still required a
  completion-bound retry near the end.

Decision:

- Do not enable the current NG preprobe knobs in the 10-task mainline config.
  They are now verified to execute, but this current dispatch pattern still
  behaves like an extra worker rather than a certificate-cost reducer.
- Future NG work should target a stronger relaxed certificate or more selective
  activation, not simply re-enable the old 10-task NG preprobe defaults.

## 2026-06-07: Hidden-Negative Profile Catalog Seeding Did Not Break Replacement Tails

Context:

- Hidden-negative audit showed that hard-case hidden task sets were usually
  present in the ordinary worker's profile universe, but still failed to become
  returned true-RC negative columns.
- The code has an exact-safe worker repair hook,
  `journey_hidden_negative_profile_catalog_seed_enabled`, which can seed
  sorties from true-dual hidden negative journeys back into the profile catalog.
  It cannot certify anything; it only tries to make later workers stop missing
  columns already discovered by the final judge.

Probe:

- Result file:
  `BPC_future/results/probe_catalog_seed_tranq10_10_20260607.csv`.
- Instance:
  `tranquillitatis_balmer_like_20km_tasks10_10_seed11162`.
- Override:
  `journey_hidden_negative_profile_catalog_seed_enabled=True`.

Observed behavior:

- Outcome remained root `TIME_LIMIT`, with the same incumbent and column count.
- The hook did execute once after a completion-bound retry:
  `journeys_seen=3`, `trips_seen=3`, `seeded_profiles=3`,
  `forced_seed_profiles=2`, and catalog size increased from `19233` to
  `19236`.
- It did not prevent the later tail from entering another completion-bound
  retry; the run ended with an incomplete CB call near the 120s limit.

Decision:

- Keep profile-catalog seeding disabled by default.  Current evidence says the
  hard tail is not primarily caused by missing physical profile catalog entries.
- Revisit only if a bounded hidden-negative audit shows actual catalog misses,
  not merely profile/materialization objective misses.

## 2026-06-07: Duplicate-Only Early Audit Helps Branch Tails, But Is Not The Main Hard-Case Fix

Context:

- Several 10-task Apollo branch logs showed expensive completion-bound final
  probes returning `DUPLICATE_ONLY`: the true-dual direct-label search exhausted
  and all negative candidates were already represented in the current branch
  RMP pool.
- The code already had an exact-safe audit,
  `_journey_promote_duplicate_only_final_judge_certificate()`, which re-solves
  the current branch RMP with variable reduced costs and accepts the duplicate
  tail only when every negative-RC existing variable is already fixed at its
  upper bound, or no existing variable has negative reduced cost.
- Some branch retry paths did not call this audit immediately after the first
  duplicate-only final judge.  They could continue into hidden patrol or a
  second cached completion-bound pass under the same RMP state.

Implementation:

- Root and branch retry/final-probe paths now promote exhausted duplicate-only
  final judges immediately before deciding whether another worker/final probe
  is needed.
- This does not change the official certificate rule: only the duplicate-only
  audit can promote the result to `CERTIFIED_NO_NEGATIVE`; rejected duplicate
  tails remain uncertified.

Probe evidence:

- Positive branch-tail probe:
  `BPC_future/results/probe_duplicate_promote3_apollo10_05_20260607.csv`.
  `apollo15_20km_tasks10_05_seed11073` stayed exact (`OPTIMAL`,
  `gap=0`, `pricing_incomplete_nodes=0`) and improved from the full-run
  snapshot around `66.21s` to about `58.02s`.  The repeated cached
  duplicate-only completion-bound call disappeared; node 2 closed with a normal
  `CERTIFIED_NO_NEGATIVE` final judge.
- Negative/mixed branch probe:
  `BPC_future/results/probe_duplicate_promote_apollo10_04_20260607.csv`.
  `apollo15_20km_tasks10_04_seed11055` remained `TIME_LIMIT` at about
  `120.01s`, with the same `0.068486` gap.  The run did accept four
  duplicate-only audits, but it still ended with deep node incomplete pricing
  (`node 9`, depth `3`, final judge `INCOMPLETE_LIMIT`, best RC about
  `-54.6671`).
- Full 5-task rerun:
  `BPC_future/results/all_tasks05_duplicate_promote_20260607.csv` solved
  `20/20` exactly, average about `0.933s`, max about `1.889s`.  All optimal
  rows had a true-dual global certificate and `pricing_incomplete_nodes=0`.
- Full 10-task rerun:
  `BPC_future/results/all_tasks10_duplicate_promote_20260607.csv` solved
  `14/20` exactly, up from the previous `13/20` snapshot.  Average time was
  about `73.169s`, max about `120.011s`, and `13` instances remained over
  `60s`.  All `14` optimal rows had a true-dual global certificate and
  `pricing_incomplete_nodes=0`.
  Clear wins: `apollo10_05` moved from about `66.21s` to `59.12s`,
  `apollo10_07` from about `90.30s` to `70.55s`, and `tranq10_10` moved from
  `TIME_LIMIT` to `OPTIMAL` in about `107.83s`.  Non-wins:
  `apollo10_04` remained `TIME_LIMIT`; `apollo10_08/09` stayed over `60s`;
  most root-tail Tranquillitatis failures were unchanged; `tranq10_05` became
  slower in this run, showing continued path sensitivity in the root tail.

Decision:

- Keep the early duplicate-only audit promotion.  It is exact-safe, removes a
  real repeated-CB pattern, and can move borderline branch cases below 60s.
- Do not treat it as the hard-case solution.  Remaining Apollo failures still
  need stronger deep-node proof/branch handling; remaining Tranquillitatis
  failures are root proof/tail problems.

## 2026-06-07: Finer 15/15 Completion-Bound Buckets Are Not Enough

Context:

- Hard Tranquillitatis roots had weak completion-bound pruning ratios.  The
  default certificate completion bound uses 10 time buckets and 10 energy
  buckets; code allows at most 15/15.
- Hypothesis: a finer resource-aware bound might increase pruning enough to
  finish the root certificate.

Probe:

- Result file:
  `BPC_future/results/probe_cb15_tranq10_06_20260607.csv`.
- Instance:
  `tranquillitatis_balmer_like_20km_tasks10_06_seed11090`.
- Overrides:
  `journey_certificate_completion_bound_time_buckets=15` and
  `journey_certificate_completion_bound_energy_buckets=15`.

Observed behavior:

- Outcome remained root `TIME_LIMIT`, about `118.07s`, same incumbent and
  column count as the 10/10 default run.
- The finer table did build a tighter/larger bound: two-cycle states increased
  from about `83,853` to `177,408`, and labels after bound fell from about
  `685,096` to `579,167`.
- The build cost also increased from about `1.47s` to `3.26s`, and the final
  judge still did not certify.

Decision:

- Do not raise the default completion-bound buckets to 15/15 based on this
  single signal.  It gives modest pruning improvement but not enough to solve
  the hard root, while increasing table size and build time.
- Revisit only if combined with a stronger final-judge ordering or a better
  resource lower bound that converts the additional states into a clear wall
  time reduction.

## 2026-06-07: Same-Dual Supplement Is A Useful Worker, Not A Full Tail Breaker

Context:

- Full 10-task reruns still showed hard roots timing out after repeated
  true-dual pricing calls.  Logs indicated a degenerate-face pattern: small
  exact batches are added, the RMP is re-solved immediately, and simplex can
  jump to a different dual extreme before the current true-dual search has
  harvested enough related columns.
- A bounded same-dual supplement was added as a worker-only mechanism.  After
  a small true-dual exact batch in the certificate tail, it runs one short
  direct-label pass under the same true dual before the RMP is re-solved.  It
  uses resource coarsening and strict time/state budgets, and its no-column
  result is ignored.  It never creates an official certificate.

Implementation:

- Code path:
  `journey_same_dual_supplement_enabled`.
- Mainline default in the 5/10/20 configs is now conservative and root-only:
  one round, `0.75s`, at most `16` returned journeys, `50/50` coarse
  time/energy buckets, and bounded DP states.
- Exactness contract is unchanged: official close still requires a fresh
  true-dual final judge with `CERTIFIED_NO_NEGATIVE`,
  `global_certificate=True`, and `pricing_dual_source=scip_certificate`.

Probe evidence:

- Positive hard-case probe:
  `BPC_future/results/probe_same_dual_main_tranq10_10_20260607.csv`.
  `tranquillitatis_balmer_like_20km_tasks10_10_seed11162` changed from the
  earlier mainline `TIME_LIMIT` at about `112.246s` to `OPTIMAL` in about
  `100.970s`.  The JSONL audit found a true-dual completion-bound certificate.
  The supplement triggered twice and added `2` replacement columns, one of
  which touched active support.
- Negative/mixed hard-case probe:
  `BPC_future/results/probe_same_dual_supplement_tranq10_01_20260607.csv`.
  `tranquillitatis_balmer_like_20km_tasks10_01_seed11000` remained
  `TIME_LIMIT` at about `119.222s`.  The supplement triggered three times and
  added `5` replacement columns, but none touched active support.
- 5-task safety check:
  `BPC_future/results/all_tasks05_same_dual_main_20260607.csv` solved
  `20/20` exactly, average about `0.952s`, max about `1.931s`.  The supplement
  did not trigger on the 5-task set.
- Full 10-task mainline rerun:
  `BPC_future/results/all_tasks10_same_dual_main_20260607.csv` again solved
  `13/20` exactly, with `7/20` `TIME_LIMIT`.  Average time moved from the
  previous `74.135s` snapshot to about `72.858s`, and instances over `60s`
  moved from `14` to `13`.  The supplement triggered `22` times and added
  `33` columns, but only `1` active-support-related changed task set was
  recorded.  This confirms the worker has small positive signal but does not
  yet address the core hard-tail failure.

Decision:

- Keep the conservative same-dual supplement enabled in the main configs as a
  Level-2.5/3.5 worker.  It has a real exact-safe positive case and did not
  disturb the 5-task benchmark.
- Do not treat it as the hard-tail solution.  The remaining bottleneck is still
  active-support impact under degenerate true duals.  Full 10-task A/B must be
  rerun before increasing budgets or widening the trigger.

## 2026-06-07: No-Negative Profile Materialization Is Not A Tail Breaker

Context:

- Fresh full 10-task logs showed the hard Tranquillitatis roots entering long
  flat tails: `objective_delta=0`, `support_changed=false`, but
  `scip_dual_l1_delta` often remained between tens and hundreds.
- Profile/exact worker rows already exposed dormant fields for
  `profile_no_negative_true_rc_materialization_*`; the hypothesis was that a
  bounded true-RC materialization pass could repair local profile no-column
  outcomes before invoking the expensive completion-bound judge.

Probe:

- Result file:
  `BPC_future/results/probe_no_negative_materialization_tranq10_01_20260607.csv`.
- Instance:
  `tranquillitatis_balmer_like_20km_tasks10_01_seed11000`.
- Overrides:
  `journey_pricing_profile_no_negative_true_rc_materialization_slack=5.0`,
  `journey_pricing_profile_no_negative_true_rc_materialization_max_candidates=64`,
  `journey_pricing_late_profile_no_negative_true_rc_materialization_slack=5.0`,
  and
  `journey_pricing_late_profile_no_negative_true_rc_materialization_max_candidates=64`.

Observed behavior:

- Outcome remained root `TIME_LIMIT`: wall time about `116.824s`,
  no dual bound, `columns=438`.
- The feature was active and did real work:
  `profile_no_negative_materialization_candidate_count` summed to `2776`,
  with `76` selected-for-scan candidates and `24` selected candidates.
- It shifted work away from CB in some tail rounds and ordinary true-dual exact
  pricing returned larger batches, e.g. `25`, `14`, `9`, and `7` journeys in
  later rounds.
- The batches still mostly missed active LP support.  Compared with the
  current baseline on the same instance, total added columns fell from `228`
  to `177`, active changed task sets fell from `13` to `3`, and the run still
  ended without a true-dual certificate.

Decision:

- Do not enable no-negative profile materialization by default in the 5/10/20
  mainline configs.  It can repair some worker-local no-column events, but on
  the hard root it mainly produces more inactive or replacement-heavy columns
  and does not move the degenerate LP face enough to certify.
- Keep it as a bounded diagnostic knob for hidden-negative audits.  Revisit
  only if a future audit shows that the missed negative columns are true-RC
  materialization misses that also change active support.

## 2026-06-07: Relaxing Pricing Epsilon To 1e-5 Does Not Remove The Hard Tail

Context:

- Several late hard-case rows reported only numerically weak negative values
  around `best_reduced_cost=-1e-06`.  Since earlier design discussions accepted
  certificate thresholds on the order of `-1e-5`, it was plausible that the
  solver was wasting the tail on numerical dust.

Probe:

- Result file:
  `BPC_future/results/probe_pricing_eps1e5_tranq10_10_20260607.csv`.
- Instance:
  `tranquillitatis_balmer_like_20km_tasks10_10_seed11162`.
- Override:
  `pricing_eps=1.0e-5`.

Observed behavior:

- Outcome remained root `TIME_LIMIT`: wall time about `118.096s`,
  no dual bound, `columns=383`.
- This was worse than the immediately preceding mainline rerun on the same
  instance (`112.246s`, `columns=355`, still `TIME_LIMIT`).
- Therefore the hard tail is not just a numerical tolerance artifact.  Weak
  reduced-cost dust exists, but the larger issue remains repeated flat rounds
  with inactive/replacement-heavy true-dual columns and no final certificate.

Decision:

- Do not change `pricing_eps` globally based on this probe.  Keep the tighter
  current tolerance unless a broader exactness/tolerance audit justifies a
  coordinated numerical-policy change across pricing, true-RC filtering, and
  certificate checks.
- Future work should continue to target active-support impact and stronger
  proof/worker batching rather than simply relaxing the reduced-cost threshold.

## 2026-06-07: Single-Sortie New-Task-Set Sweep Is Not A Tail Breaker

Context:

- A bounded true-dual worker was added as opt-in infrastructure:
  `journey_new_task_set_sweep_enabled`.
- It runs before fixed/replacement repair and before the final completion-bound
  judge.  It enumerates a small ranked universe of single-sortie task sets not
  currently represented in the RMP pool, true-RC filters candidates with
  `manual_journey_reduced_cost`, and always returns worker semantics
  (`status=INCOMPLETE`, `global_certificate_capable=False`).
- This serves priority 2/5 from the completion-bound design notes: repair the
  worker universe and batch-find useful columns, without changing official
  certificate semantics.

Validation:

- Focused tests passed:
  `test_new_task_set_sweep_gate_and_candidates_are_worker_only`,
  `test_new_task_set_sweep_finds_true_negative_new_task_set`, and adjacent
  fixed/replacement repair semantics tests.
- Compile check passed for `BPC_future/solver/journey_driver.py` and
  `BPC_future/tests/test_bpc_future.py`.

Hard-case probe:

- Probe file:
  `BPC_future/results/probe_new_task_set_sweep_tranq10_09_20260607.csv`.
- Instance:
  `tranquillitatis_balmer_like_20km_tasks10_09_seed11144`.
- Overrides:
  `journey_new_task_set_sweep_enabled=True`,
  `journey_new_task_set_sweep_time_limit=1.0`,
  `journey_new_task_set_sweep_top_tasks=10`,
  `journey_new_task_set_sweep_min_task_count=4`,
  `journey_new_task_set_sweep_max_task_count=6`,
  `journey_new_task_set_sweep_max_combinations=512`,
  `journey_new_task_set_sweep_max_sequences_per_task_set=720`,
  `journey_new_task_set_sweep_arc_options_per_leg=1`,
  `journey_new_task_set_sweep_max_option_combinations_per_sequence=1`,
  `journey_new_task_set_sweep_max_start_times_per_sequence=1`, and
  `journey_new_task_set_sweep_max_returned_journeys=24`.
- Outcome: still `TIME_LIMIT`, no dual bound, `columns=493`.
- The worker ran 3 times.  At `cg_iter=17` it found and added exactly `1`
  true-dual negative new task-set column
  (`best_reduced_cost=-0.935730286`, `candidate_trips=377`).  At
  `cg_iter=20` and `cg_iter=22` it found no negative columns
  (`best_reduced_cost=1.267058411` and `2.317916`).
- Completion-bound retries still had to act as worker:
  `cg_iter=13` selected `10` replacement-heavy negatives,
  `cg_iter=20` selected `1` new plus `9` replacement candidates, and
  `cg_iter=22` ended with a time-limited replacement-only negative.

Decision:

- Keep `journey_new_task_set_sweep_enabled=False` in main configs.  The
  infrastructure is exact-safe and may be useful for targeted leak hunts, but
  this single-sortie ranked sweep does not break the hard-root tail by itself.
- Do not spend another round merely widening this worker with more start times
  or path options until a hidden-negative audit shows that the missing columns
  are specifically single-sortie physical variants inside this candidate
  universe.  Otherwise it risks adding worker overhead without reducing final
  judge calls.

## 2026-06-07: Active-Priority CB Harvest Quota Has No Candidate On Tranq10-09

Context:

- The hard-tail logs showed completion-bound retries adding replacement-heavy
  task sets that were inactive relative to the current RMP support.  Existing
  code already supports `priority_task_sets` in diverse harvest selection, and
  final-judge calls pass the active support as that priority set.
- A natural probe was to enforce a small priority quota rather than changing
  the harvesting algorithm.

Probe:

- Result file:
  `BPC_future/results/probe_cb_priority_harvest_tranq10_09_20260607.csv`.
- Instance:
  `tranquillitatis_balmer_like_20km_tasks10_09_seed11144`.
- Overrides:
  `journey_certificate_completion_bound_diverse_harvest_min_priority_task_sets=2`
  and
  `journey_certificate_completion_bound_diverse_harvest_priority_overlap_threshold=1.0`.
- Outcome: still `TIME_LIMIT`, no dual bound, `columns=495`.

Log evidence:

- Completion-bound retry `cg_iter=13`:
  `harvest_candidate_negative_count=130`,
  `harvest_candidate_priority_task_set_count=0`,
  selected `10` replacement task sets, all inactive.
- Completion-bound retry `cg_iter=17`:
  `harvest_candidate_negative_count=248`,
  `harvest_candidate_priority_task_set_count=0`,
  selected `10` replacement task sets, all inactive.
- Completion-bound retry `cg_iter=23`:
  `harvest_candidate_negative_count=30`,
  `harvest_candidate_priority_task_set_count=0`,
  selected `5` replacement task sets, all inactive.

Decision:

- Do not enable the priority quota by default.  On this hard case the final
  judge's candidate pool contains no negative active-support task-set
  replacement to prioritize, so the quota is structurally ineffective.
- The issue is deeper than harvest ordering: under the current true duals, the
  negative columns found by CB live outside the active support and mostly
  replace existing inactive task sets.  Further work should target the dual
  tail/degenerate face or generate genuinely new RMP directions, not simply
  re-rank the same CB candidate pool.

## 2026-06-07: Full 5/10 Recheck And CB Soft-Return / Weak-Skip Probe

Context:

- A fresh full 5/10 run was performed on the current mainline using the
  engineering limit of `120s` for both sizes.
- Exactness was audited from JSONL logs, not only from CSV status.  A row was
  counted as exact only when `finish.status=OPTIMAL`,
  `pricing_incomplete_nodes=0`, and a true-dual `scip_certificate` pricing row
  had `pricing_state=CERTIFIED_NO_NEGATIVE` and `global_certificate=True`.

Results:

- Full 5-task:
  `BPC_future/results/all_tasks05_full20_verify_20260607.csv`.
  Result: `20/20` exact `OPTIMAL`, average `0.929892s`, maximum `1.893863s`.
- Full 10-task:
  `BPC_future/results/all_tasks10_full20_verify_20260607.csv`.
  Result: `14/20` exact `OPTIMAL`, average `73.604031s`; exact-optimal
  average `54.020612s`, exact-optimal maximum `103.556080s`.
  All `14/14` optimal rows passed the true-dual global-certificate audit.
- The six non-exact 10-task cases were:
  `apollo15_20km_tasks10_04_seed11055`,
  `tranquillitatis_balmer_like_20km_tasks10_01_seed11000`,
  `tranquillitatis_balmer_like_20km_tasks10_04_seed11054`,
  `tranquillitatis_balmer_like_20km_tasks10_06_seed11090`,
  `tranquillitatis_balmer_like_20km_tasks10_07_seed11108`, and
  `tranquillitatis_balmer_like_20km_tasks10_09_seed11144`.

Hard-root observation:

- On `tranq10_01`, the baseline timed out at root with no official dual bound:
  `columns=421`, `pricing_incomplete_nodes=1`.
- The final tail was not a certificate-contamination issue.  Completion-bound
  rows were true-dual `scip_certificate` rows, but they found small batches of
  negative columns and returned without a global certificate.

Probe 1: aggressive completion-bound elapsed soft-return

- Result file:
  `BPC_future/results/probe_cb_soft_min1_tranq10_01_20260607.csv`.
- Overrides:
  `journey_certificate_completion_bound_elapsed_soft_return_enabled=True`,
  `journey_certificate_completion_bound_diverse_harvest_soft_return_min_journeys=1`,
  `journey_certificate_completion_bound_diverse_harvest_soft_return_after_time=10.0`,
  and
  `journey_certificate_completion_bound_diverse_harvest_duplicate_saturation_after_time=10.0`.
- Outcome: still `TIME_LIMIT`, no dual bound, `columns=447`.
  Soft-return triggered twice and released more columns, but it did not close
  the certificate.

Probe 2: shorter 5s completion-bound elapsed soft-return

- Result file:
  `BPC_future/results/probe_cb_soft_min1_after5_tranq10_01_20260607.csv`.
- Same as Probe 1, but soft-return after `5.0s`.
- Outcome: still `TIME_LIMIT`, no dual bound, `columns=453`.
  Soft-return triggered three times and finished earlier (`~113.9s` logger
  time), but the run ended with weak-negative filtered ordinary exact rows and
  no final certificate.

Probe 3: weak-negative retry skip plus 5s soft-return

- Added opt-in infrastructure:
  `journey_skip_ordinary_retry_after_weak_negative_filtered`.
  It skips an ordinary retry only when the previous pricing returned no columns
  and reported `weak_negative_journeys_filtered > 0`; the following
  completion-bound final probe must still add a true negative or leave the node
  incomplete.
- Result file:
  `BPC_future/results/probe_cb_soft_min1_after5_skipweak_tranq10_01_20260607.csv`.
- Outcome: still `TIME_LIMIT`, no dual bound, `columns=453`.
  The skip fired four times and moved completion-bound probes earlier, but the
  probes still returned one replacement-heavy negative at a time and the last
  probe timed out without a certificate.

Decision:

- Do not enable aggressive elapsed soft-return or weak-negative retry skip in
  the main 10-task config based on this evidence.  They are exact-safe
  infrastructure and can reduce wasted worker time, but they do not break the
  hard-root degeneracy loop by themselves.
- The active bottleneck remains small-batch, replacement-heavy hidden-negative
  tailing under true duals.  The next useful work should target stronger
  active-support/new-task-set impact from tail columns, not another timing-only
  handoff or soft-return tweak.

## 2026-06-06: Full 5/10 Recheck And Replacement-Only Tail Notes

Context:

- A fresh full 5/10 run was performed after the current certificate-chain and
  funnel changes, using the engineering limit of `120s` for both sizes.
- Exactness was audited from JSONL logs, not only from the CSV status.  A run
  was counted as exact only when the finish row was `OPTIMAL`, the primal and
  dual bounds matched, `pricing_incomplete_nodes=0`, and at least one
  true-dual `scip_certificate` pricing event had
  `pricing_state=CERTIFIED_NO_NEGATIVE` and `global_certificate=True`.

Results:

- Full 5-task:
  `BPC_future/results/all_tasks05_full_verify_20260606.csv`.
  Result: `20/20` exact `OPTIMAL`, average `0.964253s`, maximum `2.018699s`.
  All 20 optimal rows passed the true-dual global-certificate audit.
- Full 10-task:
  `BPC_future/results/all_tasks10_full_verify_20260606.csv`.
  Result: `12/20` exact `OPTIMAL`, average `78.539142s`; exact-optimal
  average `52.002962s`, exact-optimal maximum `97.368155s`, with `7`
  exact-optimal cases above the `60s` target.  All 12 optimal rows passed the
  true-dual global-certificate audit.
- The 8 non-exact 10-task cases were:
  `apollo15_20km_tasks10_04_seed11055`,
  `tranquillitatis_balmer_like_20km_tasks10_01_seed11000`,
  `tranquillitatis_balmer_like_20km_tasks10_04_seed11054`,
  `tranquillitatis_balmer_like_20km_tasks10_05_seed11072`,
  `tranquillitatis_balmer_like_20km_tasks10_06_seed11090`,
  `tranquillitatis_balmer_like_20km_tasks10_07_seed11108`,
  `tranquillitatis_balmer_like_20km_tasks10_09_seed11144`, and
  `tranquillitatis_balmer_like_20km_tasks10_10_seed11162`.

Key diagnosis:

- The `OPTIMAL` semantics are clean: profile/local no-column is not being used
  as a global proof.  The remaining problem is performance, not certificate
  contamination.
- Most Tranquillitatis failures still stop at `nodes=1`, so the hard case is
  root pricing/certificate tail, not deep branch-tree explosion.
- Two-cycle completion-bound tables did not fall back to memoryless mode in the
  inspected hard 10-task runs.  The bottleneck is not a too-small
  `two_cycle_max_states`; the expensive part is still large direct-label /
  profile-generation frontiers and replacement-heavy hidden-negative tails.
- The newly non-exact `tranq10_05` and `tranq10_10` rows are path-sensitive.
  In paired single-instance reruns they could again become exact under the same
  mainline config, but still around `106s`.  Do not interpret one successful
  rerun as meeting the `60s` target.

Soft-return probe:

- Probe:
  `BPC_future/results/probe_cb_elapsed_soft_tranq10_10_20260606.csv`.
  Overrides:
  `journey_certificate_completion_bound_elapsed_soft_return_enabled=True` and
  `journey_certificate_completion_bound_diverse_harvest_soft_return_min_journeys=4`.
  Result: `OPTIMAL`, primal=dual=`198.033123`, about `89.18s` CSV /
  `90.86s` logger time.
- Probe:
  `BPC_future/results/probe_cb_elapsed_soft_tranq10_05_20260606.csv`.
  Same overrides.  Result: `OPTIMAL`, primal=dual=`203.414672`, about
  `106.09s` CSV / `107.40s` logger time.
- However, both probe logs reported
  `direct_label_harvest_soft_return_triggered=False` on the completion-bound
  pricing rows.  A no-override paired rerun on `tranq10_10` also solved exactly
  in about `105.99s`.

Decision:

- Do not enable the elapsed soft-return override by default from this evidence.
  The observed improvement is not causally proven by the log fields and remains
  within the hard-tail path sensitivity already seen in 10-task runs.
- A safe future revisit would need a paired multi-instance A/B run where
  `direct_label_harvest_soft_return_triggered=True` appears frequently and the
  exact-certificate count improves without increasing RMP column volume.

Replacement-repair probe:

- Probe:
  `BPC_future/results/probe_targeted_repair_tranq10_10_20260606.csv`.
  Override: `journey_replacement_repair_enabled=True`.
  Result: `OPTIMAL`, primal=dual=`198.033123`, about `106.30s`, essentially
  the same as the no-override paired rerun.

Decision:

- Keep `journey_replacement_repair_enabled=False` in the mainline configs.
  It remains exact-safe opt-in infrastructure, but this fresh targeted
  replacement-only case did not show a performance breakthrough.
- The next useful optimization should not be another broad replacement-only
  repair toggle.  Focus on reducing the cost of true-dual direct-label
  certificate/search itself or on helping the normal worker materialize the
  already-reached hidden task sets before the final judge is needed.

## 2026-06-06: Hot-Loop Micro-Optimizations Are Not A Tail Breaker

Context:

- A 60s `cProfile` run on
  `tranquillitatis_balmer_like_20km_tasks10_09_seed11144` showed the hard-case
  Python time dominated by profile/direct-label skyline and dominance checks:
  `_dominates_sortie_partial_label`, `_sortie_profile_resource_key`,
  `_dominates_sortie_profile`, `_add_sortie_profile_online_skyline`, and
  `_complete_sortie_label_profiles`.
- Two exact-safe micro-optimizations were tried:
  - avoid calling `_resource_bucket_floor` for energy dimensions when
    `energy_bucket_size <= 0`;
  - add `slots=True` to hot internal dataclasses and read already-float
    internal fields directly in hot key/dominance helpers.

Validation:

- Compile and focused tests passed:
  - `PYTHONDONTWRITEBYTECODE=1 python -m py_compile BPC_future/pricing/journey_pricing.py`
  - `PYTHONDONTWRITEBYTECODE=1 python -m unittest`
    `BPC_future.tests.test_bpc_future.BPCFutureTests.test_direct_journey_label_completion_bound_can_keep_next_sortie_cache`
    `BPC_future.tests.test_bpc_future.BPCFutureTests.test_direct_journey_completion_bound_reuses_resource_cache`
    `BPC_future.tests.test_bpc_future.BPCFutureTests.test_direct_journey_completion_bound_cache_key_ignores_fleet_dual`
- 5-task smoke:
  `BPC_future/results/probe_hotlocals_tasks5_20260606.csv`.
  Result: `OPTIMAL`, primal=dual=`102.041475`, about `1.93s`.
- Hard 10-task 60s profile:
  `BPC_future/results/profile_tranq10_09_60s_hotlocals_20260606.csv`.
  Result remained `TIME_LIMIT`, but reached a slightly better incumbent in the
  same short window (`203.263873` vs the earlier profile run's `204.629623`).
- Hard 10-task 120s probe:
  `BPC_future/results/probe_hotlocals_tranq10_09_20260606.csv`.
  Result remained root `TIME_LIMIT`, primal `203.102839`, no dual bound,
  about `119.22s`, `columns=495`.

Decision:

- Keep the local-field / no-energy-bucket optimization if subsequent tests stay
  green: it is exact-safe, reduces some hot function overhead, and does not add
  diagnostics or material memory pressure.
- Do not treat it as solving the 10-task hard tail.  The proof bottleneck is
  still algorithmic: ordinary worker/profile rounds and completion-bound final
  probes keep spending the full root budget before a global certificate is
  reached.
- A skyline-resource-key list-cache variant was tested during the same session
  and reverted because it added list-allocation overhead inside
  `_add_sortie_profile_online_skyline` without reducing wall-clock time.
- A `_SortieProfile.resource_key` cached-field variant was also tested and
  reverted.  It reduced repeated `round(...)` calls, but did not improve the
  60s hard-case wall-clock and added one tuple per profile, which is the wrong
  tradeoff before 20-task memory probes.

## 2026-06-06: Patrol Time Slice Slimming Helps Small Cases But Is Not A Tail Breaker

Context:

- Full 5/10 logs showed `exact_hidden_negative_patrol` and
  `exact_hidden_negative_patrol_after_retry` were repeatedly called as a
  worker-only Level 2.5 oracle, but produced no columns in the full 5-task run
  and no columns in the previous full 10-task run.  They are never certificate
  oracles, so reducing their time slice does not affect exactness; the true-dual
  completion-bound final judge remains responsible for official no-negative
  proof.
- Mainline configs were adjusted uniformly rather than per instance:
  - 5-task and 10-task: `journey_hidden_negative_patrol_time_limit` from `0.25`
    to `0.05`;
  - 20-task smoke: from `0.5` to `0.1`.

Validation:

- Full 5-task run:
  `BPC_future/results/all_tasks05_patrol_slice_20260606.csv`.
  Result: `20/20` exact `OPTIMAL`, average `0.974294s`, maximum `2.040418s`.
  Log audit: `20/20` have a true-dual `CERTIFIED_NO_NEGATIVE` global
  certificate and `pricing_incomplete_nodes=0`.
- The same 5-task instances before this slice change averaged about `1.107696s`.
  Patrol generation time dropped from about `3.78s` aggregate to about `1.03s`
  aggregate, with zero patrol-found columns in both runs.
- Hard 10-task probe:
  `BPC_future/results/probe_patrol_slice_tranq10_09_20260606.csv`.
  Result remained root `TIME_LIMIT`, primal `203.102839`, no dual bound,
  `116.317346s`, `columns=495`.  Patrol itself was cheap
  (`~0.05s` per call) and found one negative column, but the run still timed out
  in the same true-dual completion-bound / replacement-heavy tail.

Decision:

- Keep the shorter patrol time slice in the main configs.  It preserves the
  multi-level funnel while avoiding repeated 0.25s/0.5s empty patrol calls.
- Do not treat this as solving 10-task or 20-task.  The active bottleneck is
  still completion-bound final-judge search and ordinary exact/profile worker
  time, not the Level 2.5 patrol.

## 2026-06-06: Local Completion-Bound Micro-Caches Did Not Improve Hard 10-Task

Context:

- A local, exact-safe micro-cache was briefly tested inside direct-label
  completion-bound checks for repeated `(last, available_mask)` outgoing arc
  lower bounds and repeated positive cut reward / cut-dual calculations.  The
  cache was strictly scoped to one pricing call and did not change reduced-cost
  formulas or certificate semantics.

Observed behavior:

- 5-task smoke stayed exact:
  `BPC_future/results/probe_bound_cachemicro_tasks5_20260606.csv`,
  `OPTIMAL`, primal=dual=`102.041475`, `2.131442s`.
- Hard 10-task probe:
  `BPC_future/results/probe_bound_cachemicro_tranq10_09_20260606.csv`.
  Result remained root `TIME_LIMIT`, primal `203.102839`, no dual bound,
  about `119.08s` by CSV and `120.38s` by logger time.
- The hard probe performed more completion-bound retry work (`3` CB retries
  instead of `2`) and did not reduce the tail.

Decision:

- The micro-cache patch was reverted.  Do not reintroduce it as a mainline
  optimization unless a profiler shows those exact helper calls dominate a
  broader sample.
- This failure reinforces that hard 10-task time is spent in large direct-label
  search frontiers and replacement-heavy negative batches, not in these tiny
  helper computations.

## 2026-06-06: Diagnostic Slimming Is Engineering Hygiene, Not A Tail Breaker

Context:

- Hidden-negative audit and profile-mask diagnostics were useful while repairing
  the certificate chain, but they were still enabled in benchmark configs after
  the main failure mode had been identified.  They build per-journey RC/mask
  snapshots and profile mask sets that do not affect pricing decisions.
- Added lightweight controls:
  - `journey_hidden_negative_audit_max_logged_journeys=0` disables the
    hidden-negative audit entirely;
  - `journey_pricing_profile_mask_diagnostics_enabled=False` prevents profile
    pricing from constructing large diagnostic mask sets.
- The pricing result, true reduced-cost filtering, column generation, and
  certificate semantics are unchanged.

Validation:

- Compile and focused tests passed:
  - `python -m py_compile BPC_future/pricing/journey_pricing.py BPC_future/solver/journey_driver.py`
  - `PYTHONDONTWRITEBYTECODE=1 python -m unittest BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_required_components_fail_closed BPC_future.tests.test_bpc_future.BPCFutureTests.test_hidden_negative_audit_limits_detailed_journey_logs`
- 5-task smoke:
  `BPC_future/results/probe_diag_slim_tasks5_20260606.csv`.
  Result: `OPTIMAL`, primal=dual=`102.041475`, `2.148316s`.
- Hard 10-task probe:
  `BPC_future/results/probe_diag_slim_tranq10_09_20260606.csv`.
  Result remained root `TIME_LIMIT`, primal `203.102839`, no dual bound,
  `113.896336s`, `columns=494`.
- The hard probe log had zero
  `journey_hidden_negative_audit*` events and zero pricing events with
  profile-mask diagnostics enabled.

Decision:

- Keep diagnostic slimming in the 5/10/20 mainline configs.  It is exact-safe
  and reduces diagnostic overhead, especially before 20-task probes.
- Do not treat it as solving the 10-task hard tail.  It did not produce a
  certificate on `tranq10_09`; the remaining bottleneck is still the
  true-dual root proof / hidden-negative replacement tail.
- Re-enable the diagnostics only for targeted leak hunts, for example with:
  `--set journey_hidden_negative_audit_max_logged_journeys=8 --set journey_pricing_profile_mask_diagnostics_enabled=True`.

## 2026-06-06: Clean-Funnel Config Slimming Restores 5-Task But Not 10-Task

Context:

- The 10-task mainline had degraded after several exact-safe scheduling
  experiments were enabled by default.  The main issue was not GNN or
  completion bounds themselves, but the funnel role split: worker paths and the
  completion-bound final judge were repeatedly sharing the same "find hidden
  columns" work.
- The 5/10/20 configs were slimmed so GNN anchor and resource-aware completion
  bounds remain required, while failed scheduling experiments are opt-in:
  pre-exact completion-bound handoff disabled, skip-retry-after-pre-reserve
  disabled, hidden-negative profile catalog seeding disabled, flat weak-column
  pressure disabled, hidden patrol bounded again, and hidden patrol resource
  coarsening disabled by default.  Learning remains enabled and required.

Validation:

- Compile and focused unit tests passed:
  - `python -m py_compile BPC_future/pricing/journey_pricing.py BPC_future/solver/journey_driver.py BPC_future/learning/dual_stabilizer.py BPC_future/tests/test_bpc_future.py BPC_future/tests/test_learning_components.py`
  - completion-bound and learning component unit tests passed.
- Full 5-task run:
  `BPC_future/results/all_tasks05_clean_funnel_20260606.csv`.
  Result: `20/20` exact `OPTIMAL`, `exact_fail=0`, average `1.107443s`,
  maximum `2.132304s`.
- Full 10-task run:
  `BPC_future/results/all_tasks10_clean_funnel_20260606.csv`.
  Result: `14/20` exact `OPTIMAL`, average `78.541505s`, exact-optimal
  average `61.024790s`, exact-optimal maximum `108.877757s`.
- 10-task non-exact cases:
  - `apollo15_20km_tasks10_04_seed11055`: branch/global proof incomplete,
    `TIME_LIMIT`, primal `288.332462`, dual `268.585633`, gap `0.068486`,
    nodes `8`.
  - `tranquillitatis_balmer_like_20km_tasks10_01_seed11000`: root certificate
    incomplete, dual empty.
  - `tranquillitatis_balmer_like_20km_tasks10_04_seed11054`: root certificate
    incomplete, dual empty.
  - `tranquillitatis_balmer_like_20km_tasks10_06_seed11090`: root certificate
    incomplete, dual empty.
  - `tranquillitatis_balmer_like_20km_tasks10_07_seed11108`: root certificate
    incomplete, dual empty.
  - `tranquillitatis_balmer_like_20km_tasks10_09_seed11144`: root certificate
    incomplete, dual empty.
- Slow but exact 10-task cases over the 60s target:
  `apollo10_05`, `apollo10_07`, `apollo10_08`, `apollo10_09`,
  `tranq10_02`, `tranq10_03`, `tranq10_05`, `tranq10_08`, `tranq10_10`.

Key evidence:

- On `tranquillitatis_balmer_like_20km_tasks10_09_seed11144`, ordinary profile
  rounds repeatedly returned `partial_profile_scan_no_negative_journey`.
  Completion-bound pricing then found a negative batch near the time limit:
  `completion_bound_enabled=True`, `generated_sequences=318140`,
  `evaluated_timed_trips=53568`, `direct_label_harvest_candidate_count=385`,
  `direct_label_harvest_selected_count=20`, `dp_bound_pruned_labels=391372`,
  but this happened around `118.5s`, leaving no time to reoptimize and certify.

Decision:

- Keep the clean-funnel slimming.  It restores the 5-task target and removes
  several known-bad default scheduling paths without disabling GNN or
  completion bounds.
- Do not treat it as solving 10-task.  The remaining 10-task failures split
  into two bottlenecks:
  - root certificate incomplete on Tranquillitatis hard cases, where CB still
    finds hidden negative columns too late;
  - branch/global proof incomplete on at least `apollo10_04`, where node count
    and global bound closure dominate.
- Next optimization should make the true-dual worker find the CB-discovered
  hidden batch earlier, or make completion-bound final probing cheap enough to
  be a real certificate oracle.  Avoid re-enabling pre-exact handoff,
  hidden-profile catalog seeding, flat weak-column pressure, or unbounded
  coarsened patrol as defaults without new multi-instance evidence.

## 2026-06-06: Direct-Label Selection Cache And Profile Mask Filter Cache

Context:

- The hard 10-task `tranq10_09` probe showed repeated CPU work inside
  final-judge / direct-label harvesting and inside catalog profile filtering.
- Two exact-safe micro-optimizations were added:
  - cache `_selected_unique_task_set_candidates()` while the direct-label
    true-RC candidate list has not changed;
  - cache cover-dual sums and cut penalties by sortie task mask inside
    `_filter_sortie_profile_catalog`.
- These changes do not alter reduced-cost formulas, selected candidate
  ordering, no-column semantics, or certificate capability.

Tested behavior:

- 5-task smoke after the changes:
  `BPC_future/results/probe_mask_filter_cache_tasks5_20260606.csv`.
  Both instances stayed exact and fast: Apollo15 `2.151913s`,
  Tranquillitatis `1.412175s`, both `OPTIMAL`.
- Hard 10-task probe:
  `BPC_future/results/probe_mask_filter_cache_tranq10_09_20260606.csv`.
- Result still stayed root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=118.538191`, `nodes=1`,
  `primal=203.102839`, `columns=495`.
- The mask filter cache reduced ordinary exact/profile generation time versus
  the previous selection-cache probe (`62.02s` vs `67.93s`) with nearly the
  same generated/evaluated counts, but the run still required completion-bound
  work and did not certify the root.
- Completion-bound still selected only replacement task sets in the first retry
  (`96` true-RC candidates, `12` selected, `0` selected new task sets), and a
  later CB retry found no selected columns.

Decision:

- Keep both micro-optimizations.  They are exact-safe infrastructure and reduce
  repeated CPU work.
- Do not treat them as solving the hard tail.  The remaining bottleneck is
  still the worker/final-judge role split: ordinary exact/profile and hidden
  patrol keep finding or missing replacement-heavy physical representatives,
  while the final judge is not yet a cheap certificate oracle.

## 2026-06-06: Lowering Late Exact/Profile Batch To 16

Context:

- The hard 10-task `tranq10_09` tail spends a large amount of time in ordinary
  true-dual exact/profile generation before reaching completion-bound final
  judge calls.
- Hypothesis: lowering the late worker batch from the current larger batch size
  to `16` might return useful true-dual negative columns sooner, reduce wasted
  worker time, and let the final judge handle the remaining proof tail.

Tested behavior:

- Probe:
  `BPC_future/results/probe_late_batch16_tranq10_09_20260606.csv`.
- Overrides:
  `journey_pricing_late_early_return_negative_min_count=16`,
  `journey_pricing_late_streaming_min_negative_batch=16`, and
  `journey_pricing_late_max_returned_journeys=48`.
- Result remained root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=119.073224`, `nodes=1`,
  `primal=203.102839`, `columns=441`.
- Aggregate pricing shape shifted but did not improve:
  ordinary exact/profile still consumed about `62.76s` in profile generation and
  `8.97s` in profile DP across `18` calls, while completion-bound retry cost
  grew to about `38.99s` across `2` calls.
- The lower batch got to completion-bound retries earlier, but those retries
  still had to do heavy replacement/hidden-negative work.  It did not turn the
  final judge into a cheap certificate oracle.

Decision:

- Do not lower late exact/profile batch thresholds to `16` by default.
- The bottleneck is not simply that the worker waits too long before returning
  columns.  Lowering the batch can reduce worker columns and push more work
  into expensive completion-bound retries.
- Keep the current direction: strengthen worker materialization and final-judge
  harvesting semantics instead of using smaller late batches as a timing knob.

## 2026-06-06: New-Task-Set-Only Hidden Patrol

Context:

- The hard 10-task `tranq10_09` tail is replacement-heavy: completion-bound
  direct-label harvesting often returns many true-RC negative columns for task
  sets already represented in the RMP, while ordinary/profile workers report
  local no-column or dominated-only outcomes.
- Added an opt-in hidden-negative patrol mode,
  `journey_hidden_negative_patrol_new_task_set_only=True`.  It still uses true
  duals and remains a worker only: no-column is never a certificate.  The mode
  filters only final direct-label negative candidates whose task mask is already
  present in `dominant_task_set_costs`; it does not prune prefixes, because an
  existing-mask prefix may extend into a new task set.

Observed behavior:

- Probe:
  `BPC_future/results/probe_hidden_new_task_set_only_v2_tranq10_09_20260606.csv`.
- Result remained root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=119.247505`, `nodes=1`, `columns=499`.
- The new-only patrol ran but returned no journeys.  It found negative-looking
  direct-label directions with best rough RC around `-1.26`/`-1.10`, but after
  the new-task-set filter the pricing reason was
  `dominated_task_set_journeys_filtered`.
- Completion-bound retries were still needed and were triggered earlier
  (`cg_iter=13` and `15`) rather than eliminating the tail.

Decision:

- Keep the code path and mode diagnostics as opt-in infrastructure.
- Do not enable `journey_hidden_negative_patrol_new_task_set_only` by default in
  the 5/10/20 configs.
- This evidence reinforces the current diagnosis: the hard case is not simply
  missing new task-set discovery.  The bottleneck is the replacement-heavy
  degeneracy tail and the profile/direct-label materialization-selection gap
  before the final judge.

## 2026-06-06: Same-Task-Set Fallback Fill In Diverse Harvest

Context:

- Completion-bound direct-label harvesting in hard `tranq10_09` was rejecting
  many true-RC negative candidates as duplicate task sets.  Hypothesis: the RMP
  might need multiple physical columns for the same task set to break a
  replacement-heavy degenerate tail.
- Temporarily changed the diverse harvest selector to allow different
  signatures with the same task set during strongest/fallback fill.  The change
  was exact-safe because every accepted journey still passed true-RC filtering;
  it only changed batching.

Observed behavior:

- Probe:
  `BPC_future/results/probe_harvest_same_taskset_fill_tranq10_09_20260606.csv`.
- Result remained root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=119.279136`, `nodes=1`, `columns=484`.
- The selector did return larger CB batches in the tail:
  `cg_iter=21` selected `20` replacement columns from `26` candidates, and
  `cg_iter=22` selected `15` replacement columns from `15` candidates.
- All selected columns were still replacement task sets
  (`selected_new_task_set_count=0`), and the additional physical replacements
  did not move the hard root to a certificate within 120 seconds.

Decision:

- Keep the code as an explicit opt-in:
  `journey_certificate_completion_bound_diverse_harvest_allow_duplicate_task_sets`.
- Default remains `False`; do not enable this in the 5/10/20 configs without
  stronger multi-instance evidence.
- This was not the missing tail breaker.  It confirms that simply adding more
  same-task-set physical replacement columns can increase batch size without
  resolving the root degeneracy.

## 2026-06-06: Disabling Profile-DP Cross-Count Dominance

Context:

- Hidden-negative audit on hard `tranq10_09` often reported
  `profile_cross_count_dominance` or "reached hidden task set without negative
  candidate" for worker misses.  Hypothesis: profile-DP cross-count dominance
  might be retaining rough-cost representatives that fail true-RC filtering
  while pruning labels that would materialize to better true-RC columns.
- Added an opt-in late override:
  `journey_pricing_late_dp_cross_count_dominance_enabled`.  It defaults to
  inheriting `journey_pricing_dp_cross_count_dominance_enabled`, so the 5/10/20
  configs are unchanged unless explicitly overridden.

Observed behavior:

- A mistaken first probe disabled `journey_pricing_profile_cross_dominance`,
  which is sortie-profile filtering, not profile-journey DP cross-count
  dominance.  It did not answer the intended question.
- Correct probe:
  `BPC_future/results/probe_no_dp_cross_count_tranq10_09_20260606.csv`
  with `journey_pricing_dp_cross_count_dominance_enabled=False`.
- Late-only probe:
  `BPC_future/results/probe_late_no_dp_cross_count_tranq10_09_20260606.csv`
  with `journey_pricing_late_dp_cross_count_dominance_enabled=False`.
- Both remained root `TIME_LIMIT` around `119s`.
- The correct probe did change the shape in a useful but insufficient way:
  ordinary profile pricing found many more true-RC columns, and completion-bound
  retry count dropped to about one major retry.  However, profile-DP state and
  scan counts grew sharply, with late profile-DP calls often taking
  `1.1-1.6s` each.  The extra worker columns did not close the hard root within
  the 120s engineering limit.

Decision:

- Keep the late override as opt-in infrastructure for future tail-worker
  experiments.
- Do not disable profile-DP cross-count dominance by default.  Full or early
  disabling is too expensive and still does not certify the hard root.
- The useful follow-up is not "turn dominance off"; it is a bounded tail worker
  that keeps a small number of alternative labels per mask or selectively
  materializes near-miss labels under true RC.

Follow-up bounded-cap probe:

- Probe:
  `BPC_future/results/probe_late_no_dp_cross_cap10_tranq10_09_20260606.csv`
  with `journey_pricing_late_dp_cross_count_dominance_enabled=False` and
  `journey_pricing_profile_dp_max_labels_per_mask=10`.
- Result remained root `TIME_LIMIT` around `119s`, with `nodes=1` and roughly
  the same column count as the unbounded no-cross-count probe.
- The cap was active: late profile-DP calls logged large
  `dp_label_cap_pruned` counts, often tens of thousands per call.  It reduced
  some state growth, but profile-DP calls still commonly took about
  `1.0-1.6s` and did not remove the long tail.

Decision:

- Do not treat `max_labels_per_mask=10` plus cross-count relaxation as the
  Level-2.5 answer.
- A bounded worker still needs a more selective retention rule than a simple
  per-mask cap, for example retaining near-miss/alternative labels that are
  likely to survive true-RC materialization.

## 2026-06-06: Hidden-Negative Audit Reason Summary

Context:

- The hard 10-task `tranq10_09` run still timed out after the certificate
  status semantics were fixed.  Existing detailed hidden-negative logs were
  useful, but they only covered the first
  `journey_hidden_negative_audit_max_logged_journeys` journeys in a hidden
  batch.  That made it easy to over-read one or two examples and miss the batch
  distribution.
- Added a compact `journey_hidden_negative_audit_reason_summary` event.  It
  aggregates primary/candidate miss reasons and mask-hit counts across the
  whole hidden-negative batch, while keeping detailed per-journey payloads
  capped.  This is diagnostic only and does not affect pricing decisions or
  certificate semantics.
- Also changed the primary-reason priority so per-hidden-journey mask evidence
  beats broad global worker counters.  A global weak true-RC filter counter is
  still logged, but it should not be reported as the main reason if the hidden
  task set was actually reached by profile DP and then failed to become a
  negative candidate.

Observed behavior:

- Probe:
  `BPC_future/results/probe_hna_reason_summary_tranq10_09_20260606.csv`.
- Result remained root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=119.737471`, `nodes=1`, `columns=496`.
- The summary did not change the solve path, as intended.  It clarified the
  miss pattern:
  `hidden_negative_profile_mask_hit_count=20/20`,
  `hidden_negative_reachable_mask_hit_count=20/20`,
  `hidden_negative_all_trip_masks_profile_hit_count=20/20`, but
  `hidden_negative_negative_mask_hit_count=0/20` and
  `hidden_negative_selected_mask_hit_count=0/20`.
- The hard-case hidden negatives are therefore not primarily caused by missing
  physical sortie profiles in the ordinary catalog.  The profile worker already
  sees the relevant task and sortie masks; the gap is downstream in profile-DP
  objective/materialization/selection, where already-reached hidden task sets
  do not become true-RC negative returned columns.

Decision:

- Keep the compact reason summary and corrected primary-reason priority.
- Do not use this evidence to re-enable physical catalog seeding, larger
  profile batches, or wider materialization slack by default.  Those paths were
  already probed and did not close the hard root.
- The next worker repair should target the profile-DP objective/materialization
  layer or introduce a stronger true-dual direct-label worker that finds these
  already-reached hidden task-set directions before the final judge.

## 2026-06-06: Cross-Count-Pruned Profile Materialization Pool

Context:

- Disabling profile-DP cross-count dominance made the hard 10-task worker find
  more true-RC columns but was too expensive.  A narrower opt-in repair was
  added: keep cross-count dominance enabled, but when it prunes a near-threshold
  label, retain a bounded per-mask candidate for true-RC materialization.
- The feature is controlled by
  `journey_pricing_profile_cross_count_true_rc_materialization_slack` and
  `journey_pricing_profile_cross_count_true_rc_materialization_max_candidates`
  (with late-prefixed variants).  It is worker-only and defaults to disabled.
  It never changes certificate semantics.

Observed behavior:

- Probe:
  `BPC_future/results/probe_cross_count_materialization_tranq10_09_20260606.csv`.
- Overrides:
  `journey_pricing_late_profile_cross_count_true_rc_materialization_slack=3.0`
  and
  `journey_pricing_late_profile_cross_count_true_rc_materialization_max_candidates=64`.
- Result remained root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=118.335407`, `nodes=1`, `columns=484`.
- The pool did trigger but did not help: aggregate logs showed `39`
  cross-count materialization candidates, `39` selected for scan, and `22`
  selected by candidate filtering, while `weak_negative_journeys_filtered`
  rose to `122`.  Completion-bound retries still ran three times, with the
  final retry ending in `time_limit`.

Decision:

- Keep the code path as opt-in diagnostic/repair infrastructure.
- Do not enable cross-count-pruned materialization in the 5/10/20 mainline
  configs.  The evidence says this captures mostly weak true-RC candidates, not
  the missing high-value worker columns.
- The next direction should not be another materialization-slack variant.
  Move to a stronger tail dual-center worker or a more global direct-label
  patrol that still keeps final certification on the true-dual judge.

## 2026-06-06: NG/DSSR Profile Front-End As Default Worker

Context:

- Earlier NG/DSSR "flag-only" probes did not actually run the NG front-end:
  profile-pricing dispatch ignored
  `direct_journey_label_ng_probe_certificate_enabled` as a trigger when
  `direct_journey_label_ng_exact_probe_enabled` was false.
- The dispatch was fixed so probe-certificate mode can start the NG/DSSR
  front-end.  This is a correctness/semantics fix for the configurable funnel,
  not a default performance decision.

Observed behavior:

- Probe with min early-return batch `4`:
  `BPC_future/results/probe_ng_dispatch_fix_120_tranq10_09_20260606.csv`.
- Result remained root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=119.048082`, `nodes=1`, `columns=504`.
- NG now really ran (`39` exact pricing rows with
  `ng_relaxation_enabled=True`), but the solve made more RMP iterations
  (`43` vs `28`) and ordinary exact/profile still spent about `70.49s` in
  profile generation plus about `32.94s` in profile DP.

- Probe with min early-return batch `1`:
  `BPC_future/results/probe_ng_dispatch_min1_120_tranq10_09_20260606.csv`.
- Result remained root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=119.057995`, `nodes=1`, `columns=468`.
- This reduced ordinary exact/profile DP scans sharply, but RMP iterations grew
  to `55`; the completion-bound retry then consumed about `37.15s` and still
  did not prove the node.

Decision:

- Keep the dispatch fix and regression test so NG probe controls do what their
  names say.
- Do not enable NG/DSSR as a default profile front-end in the 5/10/20 mainline
  configs yet.  In current form it either fails to replace expensive profile
  work or returns too few directions and creates many extra RMP iterations.
- Revisit only if NG harvesting can return a stronger, diverse true-RC batch
  rather than one local patch per RMP round.

## 2026-06-06: Streaming Callback Backoff

Context:

- Hard 10-task `tranq10_09` spends a large share of wall-clock in ordinary
  exact/profile worker generation and profile-DP scans.
- A worker-only callback backoff was added as an opt-in code path:
  when streaming profile callbacks repeatedly return no usable true-RC batch,
  the next callback checkpoint can be delayed by 2x/4x batches.
- This is exact-safe as a worker scheduler because it only changes when a local
  profile worker asks the journey DP for columns; it does not change reduced
  costs and does not certify no-column results.

Observed behavior:

- Probe:
  `BPC_future/results/probe_stream_callback_backoff_120_tranq10_09_20260606.csv`.
- Result remained root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=119.022576`, `nodes=1`, `columns=496`.
- Aggregate shape was essentially unchanged from the scalar-precheck baseline:
  ordinary exact/profile still spent about `67.43s` in profile generation,
  about `19.36s` in profile DP, and scanned about `3.21M` profile records.
- Completion-bound retry still appeared twice; the first retry returned only
  replacement task sets and the last retry timed out.

Decision:

- Keep the code path as opt-in infrastructure, but do not enable
  `journey_pricing_streaming_callback_backoff_enabled` by default in the
  5/10/20 mainline configs.
- The evidence suggests the current expensive callbacks are already productive
  enough to return batches; the cost source is physical profile generation and
  repeated full-catalog worker DP, not empty callback churn.

## 2026-06-06: Completion-Bound Minimum Probe Time

Context:

- Baseline hard 10-task logs showed a final completion-bound retry starting
  with only about `3.23s` of probe budget.  The two-cycle table build alone took
  about `2.05s`, leaving too little search time for the final judge to either
  harvest useful columns or certify no-negative status.

Observed behavior:

- Probe:
  `BPC_future/results/probe_cb_min6_120_tranq10_09_20260606.csv`.
- Temporary override:
  `journey_certificate_completion_bound_after_retry_min_time=6.0`.
- Result remained root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=116.063677`, `nodes=1`, `columns=506`.
- The useless last completion-bound retry was skipped, reducing wall time from
  about `119s` to about `116s`, but ordinary exact/profile and profile retry
  still ended incomplete without a proof.

Decision:

- Keep a larger minimum final-probe time in the main 10/20 configs as
  scheduling hygiene.  It prevents the final judge from spending most of a tiny
  remaining budget building a bound table.
- Do not treat this as a performance breakthrough.  The hard-case proof still
  requires stronger direct-label completion bounds or fewer ordinary
  exact/profile tail loops.

## 2026-06-06: Delaying Late Profile Worker Batch

Context:

- Current hard 10-task logs show expensive early physical profile generation,
  especially around `cg_iter=6-8`, where the late profile worker waits for large
  batches and one call can spend more than `20s` before returning only a few
  useful RMP columns.
- Hypothesis: delay `journey_pricing_late_max_returned_min_cg_iter` from `3`
  to `9`, so early/mid profile workers return smaller batches sooner and leave
  more time for the final true-dual judge.

Observed behavior:

- Probe:
  `BPC_future/results/probe_late_batch_cg9_120_tranq10_09_20260606.csv`.
- Temporary override:
  `journey_pricing_late_max_returned_min_cg_iter=9`.
- Result remained root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=119.075689`, `nodes=1`, `columns=454`.
- Ordinary exact/profile calls dropped from `23` to `13`, and profile DP time
  dropped from about `21.49s` to `6.46s`, but completion-bound retry time grew
  sharply to about `44.33s`.
- The run shifted work from profile worker to the final judge rather than
  reaching a certificate.  The second completion-bound retry consumed the
  remaining tail and still did not prove the node.

Decision:

- Do not delay late profile batch activation by default in the 5/10/20
  mainline configs.
- The standalone strategy "run less profile and let CB take over earlier" is
  not enough.  If revisited, it must be paired with a stronger or more bounded
  completion-bound final judge.

## 2026-06-06: Certificate Learning Strong True-RC Filter As Tail Breaker

Context:

- Hard 10-task `tranq10_09` still shows a flat-objective tail with large dual
  movement.  Learning remained enabled in certificate-candidate rounds, but it
  could admit weak true-RC replacement columns such as about `-0.34`, which can
  perturb the RMP basis without moving the objective.
- A stricter certificate-candidate learning filter was added: learning is not
  disabled, but in tail rounds it uses a stronger true-RC threshold and disables
  weak fallback fill.  This is exact-safe because all accepted columns are still
  checked under the latest true duals, and certificates still come only from the
  true-dual judge.

Observed behavior:

- Probe:
  `BPC_future/results/probe_learning_certstrong_120_tranq10_09_20260606.csv`.
- Result remained root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=118.093391`, `nodes=1`, `columns=496`.
- The filter behaved as intended: after the first regular learning round,
  certificate-candidate filtering used threshold `1.0`, rejected the weak
  `-0.337611` learning column, and kept only stronger true-RC learning columns.
- The global bottleneck did not move enough: ordinary exact/profile still made
  `23` calls with about `67.17s` profile generation and `21.49s` profile DP;
  completion-bound retry still appeared twice and the node was not certified.

Decision:

- Keep the stronger certificate learning filter as learning hygiene and logging
  clarity.  It prevents learning from acting as a weak tail breaker while still
  keeping GNN pricing active.
- Do not keep increasing this threshold as the main performance strategy.  The
  hard 10-task bottleneck is still ordinary exact/profile catalog generation
  plus replacement-heavy true-dual tail batches.

## 2026-06-06: Physical Catalog Precheck Before Expansion

Context:

- Hard 10-task probe `tranquillitatis_balmer_like_20km_tasks10_09_seed11144`
  showed ordinary exact/profile worker generation dominates wall-clock.
- A worker-only shortcut was tested: when the dual-independent physical catalog
  hits, run the streaming profile DP on the already-built catalog before
  expanding another profile batch.
- The shortcut is exact-safe because it can only return true-RC filtered
  negative journeys; a miss still continues normal worker expansion and never
  certifies no-column status.

Observed behavior:

- Probe:
  `BPC_future/results/probe_catalog_precheck_120_tranq10_09_20260606.csv`.
- Result still timed out at the root:
  `status=TIME_LIMIT`, `primal_bound=203.102839`, `dual_bound=null`,
  `columns=482`.
- Some exact rounds returned from the existing catalog with near-zero
  generation time, but the run made more exact/profile calls (`27` vs `23`) and
  fewer total useful columns (`208` added vs `231` in the current baseline).
- Exact/profile generation time increased rather than decreased in aggregate
  (`76.1s` vs about `67.1s`), because the same partial catalog was repeatedly
  consumed before enough new physical profiles were generated.

Decision:

- Do not enable or keep the pre-expansion physical-catalog callback shortcut.
- The profile worker should continue advancing the physical catalog in batches
  before running the expensive journey DP, unless a future policy can prove it
  avoids repeated consumption of the same partial catalog.
- Revisit only with a monotone progress gate, such as minimum new profile-count
  growth since the last successful catalog-based worker return.

## 2026-06-06: Profile True-RC Materialization Slack As Default

Context:

- Hidden-negative audit on the hard 10-task instance showed profile-DP could
  reach the same hidden task masks and had all sortie masks in the physical
  catalog, but the profile-level objective for those masks was often between
  `0.0` and about `2.7` while direct-label true RC was negative.
- A bounded opt-in window was added:
  `journey_pricing_profile_true_rc_materialization_slack`.  It keeps at most
  one near-zero profile-DP candidate per final task mask and materializes it
  before applying `manual_journey_reduced_cost`.

Tested behavior:

- Hard 10-task probe with slack `3.0`:
  `tranquillitatis_balmer_like_20km_tasks10_09_seed11144_logical_graph.json`.
- A 30-second probe confirmed the window was active: by CG iteration 7,
  ordinary exact/profile had `91` materialization candidates and selected `28`
  for true-RC instantiation without an obvious early profile-DP blowup.
- A 120-second probe still timed out at the root:
  `status=TIME_LIMIT`, `primal_bound=203.102839`, `dual_bound=null`,
  `columns=495`.
- The tail still invoked completion-bound retry twice.  Ordinary profile calls
  produced many materialization candidates (`940` exact/profile candidates,
  `214` selected), but most useful-looking candidates became duplicate or
  dominated-task-set outcomes rather than new RMP directions.

Decision:

- Keep the materialization-slack code path and logging as opt-in diagnostic or
  worker-repair tooling.
- Do not enable `journey_pricing_profile_true_rc_materialization_slack=3.0` by
  default in the 5/10/20 mainline configs.
- If revisited, combine it with a repair of duplicate/dominated task-set
  filtering semantics or a targeted task-mask diversity rule; do not simply
  widen the slack window.

## 2026-06-06: JourneyPool Current-Signature Cleanup

Context:

- The journey pool used task-set dominance and, when a cheaper physical
  representative replaced an existing same-task-set journey, the old signature
  remained in `by_signature` and pointed to the new journey.
- This could make duplicate diagnostics and add semantics talk about stale
  physical routes that were no longer actual RMP columns.

Change:

- `JourneyPool.by_signature` now represents only current stored journey
  signatures.  Dominated same-task-set candidates are returned as unchanged
  without permanently adding their signature to the index, and replacement
  removes the old stored signature before inserting the new one.

Tested behavior:

- Unit tests updated the pool invariant and still pass.
- Hard 10-task probe:
  `BPC_future/results/probe_pool_signature_current_only_120_tranq10_09_20260606.csv`.
- Result remained root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=118.14621`, `nodes=1`, `columns=497`.
- Tail structure stayed the same: `23` ordinary exact/profile calls, `4`
  hidden-negative patrol calls, `2` completion-bound retries, with the first
  CB returning `15` replacement-only journeys.

Decision:

- Keep the cleanup because it makes the pool index and diagnostics match the
  actual RMP column set.
- Do not treat it as a performance breakthrough.  The hard-case bottleneck is
  still repeated ordinary exact/profile work plus replacement-heavy
  direct-label/CB tail batches.

## 2026-06-05: Dual-Specific Profile Repair Worker

Context:

- Hard 10-task probe:
  `tranquillitatis_balmer_like_20km_tasks10_09_seed11144_logical_graph.json`.
- The ordinary profile worker often reached the same hidden-negative sortie
  task mask, but its physical representative was weaker than the direct-label
  or completion-bound journey.
- A Level-2.7 repair worker was implemented to run true-dual profile labeling
  with physical catalog resume disabled and only a local cache.

Tested behavior:

- When repair ran before hidden-negative patrol, it was called 5 times, found
  0 negative journeys, and consumed about 2 seconds per call.
- Moving repair after hidden-negative patrol reduced calls from 5 to 2 and
  restored most of the lost time, but it still found 0 negative journeys.
- The effective worker remained hidden-negative patrol; the expensive fallback
  remained completion-bound final judge.

Decision:

- Keep `_journey_profile_repair_config` as an opt-in diagnostic/experimental
  worker.
- Do not enable `journey_profile_repair_enabled` by default in the 5/10/20
  mainline configs.
- If revisited, require evidence that it finds true-RC negative journeys before
  raising its time budget.

## 2026-06-05: Tail Dual Averaging As Default

Context:

- Tail objective flatness and large dual movement suggested using a sliding
  average of recent true RMP duals as a dual center.
- The implementation is exact-safe only when average-dual candidates are
  filtered by latest true-dual reduced cost and final certification still uses
  latest true duals.

Observed behavior from prior probe:

- Without feedback cooldown, dual averaging activated many times and produced
  many candidates, but only a small number survived true-RC filtering.
- With strict cooldown, activation count dropped, but useful true-RC columns
  also dropped.
- The hard-case bottleneck remained ordinary exact/profile generation and the
  final proof tail.

Decision:

- Keep dual averaging code and feedback cooldown available.
- Do not enable `journey_dual_averaging_enabled` by default in the main 5/10/20
  configs until a new probe shows consistently higher kept true-RC columns
  without inflating the RMP or delaying final certification.

## 2026-06-05: Hidden Patrol After Small Exact Batches

Context:

- The hard 10-task tail often had ordinary true-dual exact/profile pricing add
  only 1-2 columns while the RMP objective stayed flat.
- A worker-only supplement was implemented to call hidden-negative patrol after
  such small batches, before returning to the RMP.

Tested behavior:

- On the hard 10-task probe, the supplement triggered twice.
- It added 0 new journeys.
- One call found a negative reduced-cost candidate, but it was filtered by
  existing dominated task-set logic, so it did not widen the RMP.
- Wall-clock remained near the prior timeout and the root node still failed to
  certify within 120 seconds.

Decision:

- Keep `journey_hidden_negative_patrol_after_small_batch_enabled` as an opt-in
  experiment.
- Do not enable it by default in the 5/10/20 mainline configs.
- If revisited, first inspect whether `dominant_task_set_costs` is filtering
  physically useful variants too aggressively in the tail.

## 2026-06-05: Larger Late Exact Batches

Context:

- The hard 10-task root tail repeatedly added small true-dual batches after
  the RMP objective had already flattened.
- A probe increased late exact/profile batch sizes:
  `journey_pricing_late_max_returned_journeys=96`,
  `journey_pricing_late_early_return_negative_min_count=64`, and
  `journey_pricing_late_streaming_min_negative_batch=64`.

Observed behavior:

- The probe reduced RMP solves to 16 and returned large 64-column batches in
  cg3-cg7.
- It still timed out at the root within 120 seconds:
  `status=TIME_LIMIT`, `columns=593`, `pricing_calls=38`,
  `exact_pricing_calls=22`, `primal_bound=203.102839`, `dual_bound=null`.
- After cg9 the objective remained flat at `203.102839`. The solver still
  needed hidden-negative patrol and completion-bound retry to search for weak
  tail columns.
- The final completion-bound retry started at cg16 with about 20 seconds
  remaining, pruned many labels, but still returned `INCOMPLETE_LIMIT`.

Decision:

- Do not raise late batch sizes by default. Larger batches help early
  discovery but do not solve the tail certificate bottleneck on the hard case.
- If revisited, use an adaptive rule tied to objective movement and RMP column
  growth, not a static global batch increase.

## 2026-06-05: More Aggressive Completion-Bound Harvesting

Context:

- Completion-bound final judge was tested with larger harvesting targets:
  `min_journeys=48`, `max_returned_journeys=64`, `min_fill=48`, and elapsed
  soft return disabled.

Observed behavior:

- The hard 10-task probe still timed out at the root within 120 seconds.
- The completion-bound call spent more time in the final judge, selected only
  about 20 true-RC negative columns before the run hit the limit, and did not
  produce a certificate.

Decision:

- Do not simply raise final-judge harvesting targets or disable elapsed soft
  return by default.
- More columns from the final judge are useful only if the judge can reach and
  harvest them early enough. The next improvement should reduce the cost of
  reaching certificate-quality search states, not just increase the requested
  return count.

## 2026-06-05: Cross-Count-Relaxed Profile Repair

Context:

- Hidden-negative audit repeatedly reported `profile_cross_count_dominance`
  among the likely worker miss causes on the hard 10-task tail.
- The Level-2.7 profile repair worker was tested with its own
  `dp_cross_count_dominance` disabled while leaving ordinary profile pricing
  unchanged.

Observed behavior:

- Hard 10-task probe:
  `tranquillitatis_balmer_like_20km_tasks10_09_seed11144_logical_graph.json`.
- The run still timed out at the root within 120 seconds:
  `status=TIME_LIMIT`, `columns=530`, `rmp_solves=18`,
  `pricing_calls=44`, `exact_pricing_calls=26`,
  `primal_bound=203.102839`, `dual_bound=null`.
- Profile repair was called twice, generated about 40k sequences per call, and
  found 0 negative journeys.
- The effective tail still fell back to hidden-negative patrol and
  completion-bound retry.

Decision:

- Keep any cross-count-relaxed repair path opt-in only.
- Do not disable cross-count dominance in ordinary profile pricing or default
  repair settings.
- The audit marker is useful for diagnosis, but the tested relaxation did not
  repair the worker.

## 2026-06-05: Pre-Exact Hidden-Negative Patrol

Context:

- Hidden-negative patrol can find columns after ordinary/profile local
  no-column, so it was tested before ordinary exact/profile in the flat tail.
- The goal was to turn patrol into a cheaper Level-2.5 worker and avoid
  repeated local no-column profile calls.

Observed behavior:

- Hard 10-task probe with
  `journey_hidden_negative_patrol_before_exact_flat_enabled=True` still timed
  out at the root.
- It produced a worse incumbent/tail value than the mainline probe:
  `primal_bound=203.263873` instead of `203.102839`.
- It increased control-flow churn: `rmp_solves=23`, `pricing_calls=54`,
  `exact_pricing_calls=31`, `columns=542`.
- Pre-exact patrol found some early weak columns, but ordinary exact and
  completion-bound retry were still needed, and the final certificate was not
  reached.

Decision:

- Do not enable pre-exact hidden-negative patrol by default.
- If revisited, require a stricter trigger than flatness alone, for example a
  recent proven hidden-negative streak plus a cap on consecutive patrol misses.
- The implementation now defaults the opt-in pre-exact patrol to require at
  least one prior no-column-followed-by-negative event, so manually enabling
  the flag no longer reproduces this broad flatness-only trigger unless the
  threshold is explicitly set to zero.

## 2026-06-05: Disabling Static SRC Entirely

Context:

- Static subset-row cuts make the root RMP stronger, but they also add cut
  duals that make true-dual journey pricing harder in the root tail.
- A hard 10-task probe tested whether removing static SRC could reduce the root
  certificate burden.

Observed behavior:

- Hard 10-task probe:
  `tranquillitatis_balmer_like_20km_tasks10_09_seed11144_logical_graph.json`.
- With `static_subset_row_cuts_enabled=False`, the root node reached a
  true-dual `CERTIFIED_NO_NEGATIVE` result around CG iteration 14.
- The bound became much weaker: `dual_bound=191.252171` while the incumbent was
  `primal_bound=203.102839`.
- The solver then had to branch and timed out at node 1 within the 120-second
  engineering limit:
  `status=TIME_LIMIT`, `nodes=2`, `columns=497`, `cuts_added=1`,
  `subset_row_cuts_added=0`, `fleet_lb_cut_added=1`.

Decision:

- Do not disable static SRC entirely in the default 5/10/20 mainline configs.
- The result confirms that static SRC is doing useful bound work even though it
  contributes to root pricing difficulty.
- If revisited, test delayed, budgeted, or ranked static SRC activation rather
  than a full off switch.  The goal should be to keep enough root bound strength
  while reducing the number of difficult cut-dual interactions in pricing.

## 2026-06-05: Static SRC Budget Sweep To 40/60

Context:

- After the full static-SRC off switch weakened the bound too much, two probes
  tested whether keeping a smaller static SRC budget could reduce pricing tail
  difficulty without losing the root bound entirely.

Observed behavior:

- Hard 10-task probe:
  `tranquillitatis_balmer_like_20km_tasks10_09_seed11144_logical_graph.json`.
- With `static_subset_row_cut_budget=60`, the run still timed out at the root:
  `status=TIME_LIMIT`, `solving_time=119.070560`, `nodes=1`,
  `rmp_solves=26`, `pricing_calls=54`, `exact_pricing_calls=28`,
  `generated_sequences=1784061`, `evaluated_timed_trips=1969935`,
  `columns=539`, `subset_row_cuts_added=60`.
- With `static_subset_row_cut_budget=40`, the run also timed out at the root:
  `status=TIME_LIMIT`, `solving_time=119.192788`, `nodes=1`,
  `rmp_solves=31`, `pricing_calls=63`, `exact_pricing_calls=32`,
  `generated_sequences=2016022`, `evaluated_timed_trips=2096407`,
  `columns=550`, `subset_row_cuts_added=40`.
- Budget 40 was worse than budget 60 on this hard case, and neither produced a
  root certificate within the 120-second engineering limit.

Decision:

- Do not continue blind static SRC budget sweeping as the next optimization
  path.
- Keep the current default budget unless a new, ranked or delayed SRC strategy
  is implemented and tested.
- If revisited, the experiment should change SRC selection quality or timing,
  not merely lower the static budget number.

## 2026-06-05: Compact-Ranked Static SRC At Budget 60

Context:

- The plain static-SRC budget sweep showed that lowering the budget alone was
  not enough.  A follow-up probe tested an opt-in ranked selection mode,
  `static_subset_row_selection=compact`, which chooses valid SRC by physical
  compactness and time-window compatibility instead of task-id lexicographic
  order.

Observed behavior:

- Hard 10-task probe:
  `tranquillitatis_balmer_like_20km_tasks10_09_seed11144_logical_graph.json`.
- With `static_subset_row_cut_budget=60` and
  `static_subset_row_selection=compact`, the run still timed out at the root:
  `status=TIME_LIMIT`, `solving_time=119.256769`, `nodes=1`,
  `rmp_solves=23`, `pricing_calls=47`, `exact_pricing_calls=24`,
  `generated_sequences=1759717`, `evaluated_timed_trips=1737076`,
  `columns=530`, `subset_row_cuts_added=60`.
- It reduced calls versus lexicographic budget 60, but did not produce the root
  certificate within the 120-second engineering limit.
- The final completion-bound call had many candidates
  (`harvest_candidate_negative_count=362`) but selected only 4 true-RC negative
  journeys before hitting the time limit.

Decision:

- Keep compact static-SRC selection opt-in only.
- Do not enable it by default from this single hard-case probe.
- If revisited, combine ranked SRC with delayed activation or a better
  final-judge harvesting trigger; ranking alone was not enough.

## 2026-06-05: Duplicate-Saturated CB Harvest Soft Return

Context:

- Compact-SRC probes showed completion-bound direct-label pricing could collect
  many true-RC negative physical candidates but very few unique RMP task-set
  directions, for example `362` candidates, `358` duplicate-task-set
  rejections, and only `4` selected journeys.
- A low-risk soft-return rule was added so a completion-bound final judge can
  return already found true-negative directions when candidate generation is
  duplicate-task-set saturated and the elapsed/remaining-time condition is met.

Observed behavior:

- Unit coverage confirms the new rule does not change no-column certificate
  semantics; it only returns already true-RC negative columns.
- On hard 10-task `tranq10_09` with the current main config, the run still hit
  the `120s` engineering limit:
  `status=TIME_LIMIT`, `solving_time=119.089363`, `nodes=1`,
  `rmp_solves=19`, `pricing_calls=44`, `exact_pricing_calls=25`,
  `generated_sequences=1645283`, `evaluated_timed_trips=1889134`,
  `columns=531`, `subset_row_cuts_added=120`.
- The rule did trigger usefully at `cg_iter=15`, returning `15` selected
  true-negative journeys from `97` candidates with `82` duplicate-task-set
  rejections.
- The final stall remained at the root.  A later ordinary exact/profile call
  became `profile_dp_incomplete` with less than one second of pricing budget
  left, after a completion-bound retry at `cg_iter=18` found only one unique
  negative journey.

Decision:

- Keep the duplicate-saturated soft return because it is exact-safe and avoids
  wasting final-judge time on repeated physical variants of the same task set.
- Do not treat it as the main breakthrough.  The next bottleneck is still
  worker/pricer quality before the final seconds: ordinary profile and the
  0.5s hidden patrol miss hard hidden negatives, while the CB retry can find
  them only after expensive direct-label search.

## 2026-06-05: CB Diverse-Harvest Soft Min Set To 1

Context:

- After adding duplicate-saturated soft return, a probe lowered
  `journey_certificate_completion_bound_diverse_harvest_soft_return_min_journeys`
  from `15` to `1` to test whether returning any true-negative CB column near
  the end of the local pricing budget would avoid final-tail starvation.

Observed behavior:

- Hard 10-task `tranq10_09` still timed out:
  `status=TIME_LIMIT`, `solving_time=118.054531`, `nodes=1`,
  `rmp_solves=23`, `pricing_calls=52`, `exact_pricing_calls=30`,
  `columns=535`.
- Compared with the current main config, it saved only about one second while
  increasing RMP/pricing iterations.  Late calls returned very small batches,
  including one-column hidden patrol/final-judge results, then the next rounds
  still required ordinary exact/profile or another final probe.

Decision:

- Do not lower the default soft-return minimum to `1`.
- The problem is not merely that CB waits too long before returning; the solver
  needs better worker/pricer quality before the final seconds so hidden
  negatives are found earlier and in more useful directions.

## 2026-06-05: Hidden Patrol With Completion Bound At 0.5s

Context:

- Ordinary hidden-negative patrol uses true duals and resource coarsening, but
  not the completion-bound table.  A probe tested whether enabling completion
  bounds and 2-cycle bounds inside the 0.5s patrol could catch hidden negatives
  before the expensive final judge.

Observed behavior:

- Hard 10-task `tranq10_09` still timed out:
  `status=TIME_LIMIT`, `solving_time=118.162874`, `nodes=1`,
  `columns=542`.
- The patrol built the completion-bound table but found no columns in its
  0.5s budget.  Example calls spent about `0.50s` just building the bound
  (`lb_state_count=1331`) with `generated_sequences=0`.
- The final completion-bound retry was still needed and found columns later.

Decision:

- Do not enable completion bounds inside the default hidden-negative patrol.
- This turns the judge machinery into a worker and spends the tiny patrol
  budget on bound construction rather than useful search.

## 2026-06-05: Profile-Labeling Priority Lookahead/Cut Weights

Context:

- Hidden routes often look like "lose early, win later", so profile-labeling
  best-first priority was extended with opt-in ordering-only knobs:
  future positive cover-dual lookahead and realized cut-dual value.  These
  knobs do not change feasibility, reduced-cost filtering, or certificates.

Observed behavior:

- `journey_pricing_profile_labeling_priority_future_dual_weight=0.5` on hard
  10-task `tranq10_09` still timed out:
  `status=TIME_LIMIT`, `solving_time=119.263900`, `rmp_solves=25`,
  `pricing_calls=52`, `exact_pricing_calls=27`, `columns=560`.
  It found more profile negative candidates (`4581` vs `3764`) but increased
  RMP/pricing iterations and column volume.
- `journey_pricing_profile_labeling_priority_cut_dual_weight=1.0` also timed
  out:
  `status=TIME_LIMIT`, `solving_time=119.064990`, `rmp_solves=28`,
  `pricing_calls=59`, `exact_pricing_calls=31`, `columns=536`.
  It reduced CB positives to one call but increased hidden-patrol and exact
  calls, so the tail was not solved.

Decision:

- Keep both priority knobs opt-in with default `0.0`.
- Do not enable either by default from these probes.  The evidence suggests
  simple heap reordering can find different columns but does not yet produce
  a shorter proof trajectory.

## 2026-06-05: Profile DP Max Labels Per Mask As Default

Context:

- Hard 10-task `tranq10_09` spends a large amount of time in ordinary
  true-dual profile DP scans after the root LP objective is already flat.
- A worker-only label cap was added as an opt-in knob:
  `journey_pricing_profile_dp_max_labels_per_mask`.  The cap is exact-safe only
  because profile no-column remains `LOCAL_NO_COLUMN_UNCERTIFIED`; final
  certification still requires the true-dual direct-label completion-bound
  judge.

Observed behavior:

- With `journey_pricing_profile_dp_max_labels_per_mask=8`, the hard 10-task
  probe still timed out:
  `status=TIME_LIMIT`, `solving_time=118.772485`, `nodes=1`, `columns=534`.
- The cap was active and pruned many profile-DP labels, but it changed the
  column trajectory in the wrong direction: pricing calls increased to `58`,
  exact pricing calls increased to `32`, and CG reached `26` iterations.
- Ordinary exact profile-DP time increased rather than decreased in aggregate
  on this run, because the reduced worker frontier returned smaller/weaker
  batches and forced more RMP/pricing rounds.

Decision:

- Keep the code path as an opt-in diagnostic/experimental worker limiter.
- Do not enable `journey_pricing_profile_dp_max_labels_per_mask` by default in
  the 5/10/20 mainline configs; keep the default value `0`.
- If revisited, use it only with an adaptive rule tied to objective flatness,
  minimum batch quality, and available final-judge time, not as a static global
  cap.

## 2026-06-05: Pre-Retry Reserve And Learning Failure Alpha Floor

Context:

- Priority 4 suggested protecting the final true-dual completion-bound judge
  from being starved by an ordinary profile/direct-label worker late in the
  120s hard-tail run.
- Priority 6 suggested keeping learning enabled while reducing anchor influence
  when smoothed pricing repeatedly returns no true-RC useful columns.

Implemented behavior:

- `journey_certificate_completion_bound_pre_retry_reserve_time` is gated by
  `certificate_candidate=True`, final completion-bound eligibility, and a low
  remaining-time threshold.  The reserve also leaves at least the ordinary
  retry minimum time, so it no longer creates sub-second worker calls.
- The 10-task mainline reserves up to `8s` when remaining time is at most
  `35s`; the 20-task smoke config reserves up to `15s` when remaining time is
  at most `180s`; 5-task remains disabled.
- `journey_learning_true_rc_filter_fail_alpha_floor` lets repeated weak
  learning rounds reduce anchor weight below `alpha_min_active` while keeping
  it positive.  Empty smoothed-pricing rounds now count as weak rounds.  The
  10/20-task configs use a `0.05` failure floor.

Observed behavior:

- On hard 10-task `tranq10_09`, pre-reserve and the learning failure floor were
  both active, but the run still timed out:
  `BPC_future/results/probe_reserve_minworker_alpha_floor_tranq10_09_20260605.csv`
  reported `status=TIME_LIMIT`, `solving_time=119.198167`, `nodes=1`,
  `columns=533`.
- The reserve no longer created meaningless sub-second ordinary calls; late
  pre-reserve calls kept ordinary worker budgets around `6.97s`, `5.16s`, and
  `3.54s`.
- Learning alpha dropped to `0.05` by `cg_iter=16`, confirming the feedback
  path works.  It still produced zero useful learning columns in the tail.
- The root LP objective remained flat at `203.102839`; the final judge harvested
  `15` columns at `cg_iter=15`, then only `1` more at `cg_iter=18`, and no
  certificate was reached before the time limit.

Decision:

- Keep the reserve minimum-worker safeguard and the learning failure floor
  because both are exact-safe and avoid obviously bad runtime behavior.
- Do not treat them as breakthrough fixes.  The remaining bottleneck is still
  the root-tail degeneracy/profile-final-judge column trajectory: workers miss
  hidden negatives or return tiny batches, and final judge harvest does not move
  the RMP objective enough.

## 2026-06-05: New-Task-Set-Aware Final-Judge Harvesting

Context:

- Hard-tail logs showed a misleading pattern: completion-bound retry logged
  many `added_journeys`, but the next RMP variable count sometimes did not
  increase.
- `JourneyPool` uses task-set dominance, so a lower-cost physical realization
  for an existing task set replaces the old representative without adding a new
  RMP variable.  This is exact-safe when cuts depend only on task sets, but it
  means a final judge can spend expensive search returning replacement-only
  batches.

Implemented behavior:

- Journey-column addition logs now split `new_journeys`,
  `replacement_journeys`, and `unchanged_journeys`.
- Direct-label diverse harvesting now receives the existing RMP task-set set
  and prefers true-RC negative candidates with new task sets before falling
  back to replacement candidates.
- Pricing logs and hidden-negative audit include candidate/selected new-task-set
  counts for completion-bound harvesting.

Observed behavior:

- On hard 10-task `tranq10_09`, the run still timed out:
  `BPC_future/results/probe_newtask_harvest_tranq10_09_20260605.csv`
  reported `status=TIME_LIMIT`, `solving_time=118.177342`, `nodes=1`,
  `columns=530`.
- The key diagnostic is decisive: at `cg_iter=15`, completion-bound harvesting
  had `harvest_candidate_negative_count=97` but
  `harvest_candidate_new_task_set_count=0`.  All `15` selected journeys were
  replacements: `harvest_selected_new_task_set_count=0`,
  `harvest_selected_replacement_task_set_count=15`.
- Column-addition logs confirm the same: `cg_iter=15`
  `exact_completion_bound_retry` requested `15`, added `15`, but
  `new_journeys=0` and `replacement_journeys=15`; the next RMP variable count
  stayed flat.

Decision:

- Keep the new/replacement split and new-task-set-aware selection because it is
  exact-safe and clarifies the tail mechanics.
- Do not continue tuning overlap thresholds, `top_k_strongest`, or harvest fill
  counts for this hard case.  The bottleneck is not selection among available
  new task sets; the final judge is not generating any new task-set directions
  at the expensive point.  Next work should target profile/direct-label
  generation so useful new task sets appear before the final seconds.

## 2026-06-06: Existing-Task-Set Replacement Repair Worker

Context:

- The `probe_newtask_harvest_tranq10_09_20260605` log showed a sharp tail
  pathology at `cg_iter=15`: ordinary true-dual profile pricing returned
  no column, hidden patrol returned no column, but completion-bound direct
  label later found `97` true-RC negative candidates.
- All `97` candidates were replacement-only:
  `harvest_candidate_new_task_set_count=0`; the selected `15` columns all
  replaced lower-cost physical realizations for existing task sets and did not
  increase the RMP variable count.
- This suggested a targeted worker: run direct-label pricing only over prefixes
  that can end in an already-known task set, so it can repair physical
  representatives before the expensive final judge.

Implemented behavior:

- `direct_journey_label_existing_task_set_repair_only` restricts direct-label
  candidates to existing journey-pool task sets and returns `INCOMPLETE` on
  no-column even if its restricted universe is exhausted.
- `_journey_replacement_repair_config` builds this as an opt-in true-dual
  worker.  It disables completion-bound certification and is not
  certificate-capable.

Observed behavior:

- Hard 10-task probe:
  `BPC_future/results/probe_replacement_repair_tranq10_09_20260606.csv`
  still timed out at the root:
  `status=TIME_LIMIT`, `solving_time=118.162824`, `nodes=1`, `columns=530`.
- The new worker triggered once at `cg_iter=15` with `known_task_sets=524`,
  `time_limit=2.0`, resource coarsening `50/50`, and
  `direct_journey_label_existing_task_set_repair_only=True`.
- It generated `1,075` sequences and evaluated `17,787` timed trips, but found
  `0` negative journeys and ended with `timed_trip_pricing_incomplete`.
- The following completion-bound retry still found the same replacement-only
  batch shape: `harvest_candidate_negative_count=97`,
  `harvest_candidate_new_task_set_count=0`,
  `harvest_selected_replacement_task_set_count=15`.

Decision:

- Keep the restricted direct-label repair code and tests as an opt-in
  experiment because it is exact-safe and has useful diagnostics.
- Do not enable `journey_replacement_repair_enabled` in the 5/10/20 mainline
  configs by default.  On the hard case it consumed proof time without finding
  the replacement columns that completion-bound direct-label found later.
- If revisited, do not merely increase its time budget.  The missing ingredient
  is likely the completion-bound-guided direct-label ordering/pruning itself,
  not only the existing-task-set restriction.

## 2026-06-06: Replacement-Only Hidden Patrol Escalates Directly To CB

Context:

- After the replacement-repair worker failed, a smaller control-flow change was
  tested: keep hidden patrol, but when it returns only replacement task sets in
  the certificate tail, do not add those small replacement-only batches to the
  RMP.  Instead, escalate immediately to the true-dual completion-bound judge in
  the same tail round.
- The hypothesis was that this would avoid repeated RMP re-solves on
  replacement-only columns and let CB harvest the larger physical-repair batch
  earlier.

Observed behavior:

- Hard 10-task probe:
  `BPC_future/results/probe_patrol_repl_escalate_tranq10_09_20260606.csv`
  still timed out:
  `status=TIME_LIMIT`, `solving_time=119.103804`, `nodes=1`, `columns=528`.
- The escalation triggered at `cg_iter=12`: hidden patrol had `3` negative
  journeys, all replacement-only, so CB ran immediately with about `41s`
  remaining.
- The early CB returned `17` replacement-only journeys:
  `harvest_candidate_negative_count=158`,
  `harvest_candidate_new_task_set_count=0`,
  `harvest_selected_replacement_task_set_count=17`.
- This did shift some new task-set discovery earlier (`cg_iter=13-15`), but it
  did not create enough RMP progress and later required another CB call at
  `cg_iter=16`, again replacement-only.  The run remained root TIME_LIMIT.

Decision:

- Keep `journey_hidden_negative_patrol_replacement_only_escalates_to_cb` as an
  opt-in diagnostic switch only.
- Do not enable it by default in 5/10/20 configs.  Simply moving CB earlier
  turns the judge into an expensive replacement worker and does not solve the
  hard-tail certificate gap.
- The next useful direction should target generation of genuinely new task-set
  directions or a stronger final proof bound, not earlier replacement-only CB
  work.

## 2026-06-06: Streaming Worker Fixed-Time Soft Return

Context:

- The hard 10-task `tranq10_09` probe showed large early exact/profile
  generation costs while trying to collect late batches of `48` true-RC
  negative journeys.
- A natural idea was to keep batch pricing, but allow profile/streaming worker
  pricing to return earlier once enough negative columns had been found after a
  fixed elapsed time.

Tested behavior:

- Temporarily set:
  `journey_pricing_streaming_partial_return_after_time = 5.0` and
  `journey_pricing_streaming_partial_return_min_journeys = 16` for the 10-task
  config, with analogous scale-based values considered for 5/20.
- Hard 10-task probe:
  `BPC_future/results/probe_stream_soft_return_tranq10_09_20260606.csv`
  remained `TIME_LIMIT` at the root:
  `status=TIME_LIMIT`, `solving_time=119.122633`, `nodes=1`,
  `columns=515`.

Observed comparison against the immediately preceding probe
`probe_late_direct_min_tranq10_09_20260606`:

- Baseline profile-worker exact calls:
  `18` calls, `68.086s` profile generation, `295` negative journeys,
  `1,362,936` generated sequences.
- Fixed-time soft-return probe:
  `18` calls, `73.444s` profile generation, `266` negative journeys,
  `1,682,319` generated sequences.
- The soft return cut some individual batches from `48` to `16`, but the
  missing columns forced later, more expensive searches.  It did not reduce
  the proof tail.

Decision:

- Reverted the fixed-time soft-return config knobs.
- Do not enable this as a default tuning path.  A useful worker-return rule must
  be state-aware, for example based on new task-set diversity, objective
  progress, or remaining certificate budget, not only elapsed wall time.

## 2026-06-06: Profile Worker New-Task-Set Early-Return Gate

Context:

- The hard 10-task `tranq10_09` tail has repeated replacement-only hidden
  patrol / completion-bound batches.  A plausible worker-side fix was to delay
  ordinary profile-worker early return until the batch contained a minimum
  number of task-set masks that were not already represented in the RMP pool.
- Implemented the gate as an opt-in config field:
  `journey_pricing_late_early_return_new_task_set_min_count`, plus lightweight
  log counters:
  `profile_negative_new_mask_count`,
  `profile_negative_selected_new_mask_count`, and
  `profile_negative_selected_replacement_mask_count`.

Tested behavior:

- Temporarily set the 10-task late new-mask gate to `4` and ran:
  `BPC_future/results/probe_newmask_gate_tranq10_09_20260606.csv`.
- Result remained root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=119.200701`, `nodes=1`, `columns=533`.
- The new counters showed the ordinary exact/profile worker was already
  returning many new task-set masks.  Examples from the hard probe:
  `cg_iter=3` returned `48` negative journeys with `42` selected new masks;
  `cg_iter=4-7` each returned `48` negative journeys with roughly `24-26`
  selected new masks.

Decision:

- Do not enable the new-task-set early-return gate in the main 5/10/20 configs.
  It did not address the current hard tail because ordinary worker batches
  already contain many new task-set directions.
- Keep the opt-in gate and counters in code.  They are useful bounded audit
  tools for future cases where the worker really is returning replacement-heavy
  batches, but the current hard `tranq10_09` bottleneck lies elsewhere.

## 2026-06-06: Journey Pool Restart On Degenerate Flat Tail

Context:

- The hard 10-task `tranq10_09` run was stuck in a flat root tail with many
  columns, large dual movement, and repeated true-dual pricing work.  A natural
  idea was to restart the journey pool after several degenerate flat rounds,
  keeping singleton safety columns, recent columns, active RMP columns, and the
  best columns per task set.
- The hypothesis was that a smaller pool would reduce RMP degeneracy and make
  subsequent pricing/RMP iterations cheaper.

Tested behavior:

- Opt-in probe:
  `BPC_future/results/probe_pool_restart_tranq10_09_20260606.csv`.
- Temporary overrides:
  `journey_pool_restart_enabled=true`,
  `journey_pool_restart_trigger=degenerate_flat`,
  `journey_pool_restart_after_degenerate_rounds=4`,
  `journey_pool_restart_min_columns=350`,
  `journey_pool_restart_keep_task_sets=140`,
  `journey_pool_restart_keep_recent=96`,
  `journey_pool_restart_max_times=2`.
- Result remained root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=119.566018`, `nodes=1`,
  `columns=319`.

Observed comparison:

- One restart fired at `cg_iter=14`, reducing the pool from `524` journeys to
  `143` kept journeys.
- Final column count fell from about `533` in the comparable hard probe to
  `319`, so the restart did remove volume.
- The lower column count did not translate into progress.  The run required
  more loop work: roughly `84` pricing calls and `46` RMP solves, versus about
  `45` pricing calls and `20` RMP solves in the comparable no-restart probe.
- The objective remained flat and the tail still showed large dual movement,
  so pool volume was not the primary bottleneck for this hard case.

Decision:

- Do not enable journey pool restart as a default optimization.  It reduces
  column count, but it can erase useful basis context and increase the number
  of RMP/pricing loops.
- Keep it as an opt-in diagnostic tool only.  A future restart rule would need
  proof that it preserves RMP progress, not merely that it shrinks the pool.

## 2026-06-06: Hidden-Negative Physical Catalog Seed

Context:

- Hidden-negative audit on hard 10-task `tranq10_09` showed ordinary
  profile/catalog pricing returning local no-column while true-dual direct
  hidden patrol or completion-bound retry found negative journeys.
- A proof-safe worker repair was implemented: whenever hidden patrol or the
  completion-bound judge returns feasible true-dual journeys, convert their
  timed sorties into fixed-start physical `_SortieProfile`s and seed the
  ordinary profile physical catalog.

Tested behavior:

- Probe:
  `BPC_future/results/probe_profile_seed2_tranq10_09_20260606.csv`.
- Result remained root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=118.160639`, `nodes=1`, `columns=530`.
- Seed logs fired at `cg_iter=11,12,13,15`, but every profile was already
  present or dominated:
  `seeded_profiles=0`, `duplicate_or_dominated_profiles=3,3,2,15`.
- Therefore the hidden negatives were not caused by missing physical sortie
  profiles in the catalog.  The ordinary worker already had the physical
  sorties; the miss is downstream in profile/journey combination, filtering,
  or dual/cut objective handling.

Decision:

- Keep the seed helper and bounded log event.  It is exact-safe and can repair
  other cases where the physical catalog is genuinely missing hidden sorties.
- A follow-up forced-seed probe retained every known hidden fixed-start sortie
  even when the profile skyline rejected it:
  `BPC_future/results/probe_forced_seed_tranq10_09_20260606.csv`.
  It did insert profiles (`forced_seed_profiles=3,3,2,15,3`) and grew the
  physical catalog from about `34,905` to `34,931`, but the run still timed out:
  `status=TIME_LIMIT`, `solving_time=119.34709`, `nodes=1`, `columns=532`.
- Do not enable `journey_hidden_negative_profile_catalog_seed_enabled` in the
  5/10/20 mainline configs by default.  Keep it as an opt-in worker-repair
  experiment and bounded audit hook.
- For the current hard `tranq10_09` tail, focus on direct-label worker strength,
  genuinely new task-set directions, or a stronger final proof bound.  Profile
  catalog seeding, even forced, did not solve the replacement-only tail.

## 2026-06-06: Disabling Profile DP Cross-Count Dominance

Context:

- Ordinary profile DP showed very large `dp_cross_count_pruned_labels`
  counters during the hard `tranq10_09` tail, while hidden direct-label patrol
  still found negative journeys.
- Hypothesis: cross-count dominance might be pruning labels that require more
  sorties or different completion structure to become negative under true
  cuts/fleet terms.

Tested behavior:

- Probe:
  `BPC_future/results/probe_no_crosscount_tranq10_09_20260606.csv`.
- Temporary override:
  `journey_pricing_dp_cross_count_dominance_enabled=false`.
- Result remained root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=118.365429`, `nodes=1`, `columns=530`.
- Hidden patrol / completion-bound pattern did not improve:
  `exact_hidden_negative_patrol=5`,
  `exact_completion_bound_retry=2`, total added columns unchanged.
- DP state count increased sharply:
  exact profile DP total `dp_state_count` rose from about `198k` to `664k`,
  while negative candidates and final progress stayed essentially unchanged.

Decision:

- Do not disable cross-count dominance in main configs.  It is not the cause of
  the current hidden negatives and it provides substantial state compression.
- If revisited later, test only a narrower tail-specific variant with clear
  evidence that it changes hidden-negative discovery, not a blanket disable.

## 2026-06-06: Completion-Bound Elapsed Soft Return And Larger Harvest

Context:

- At hard 10-task `tranq10_09` `cg_iter=15`, the completion-bound final judge
  found a replacement-only batch and returned early via diverse-harvest elapsed
  soft return.  Hypothesis: this early return might recreate the long-tail
  loop by adding only a small physical-repair batch.

Tested behavior:

- Probe without elapsed soft return:
  `BPC_future/results/probe_cb_no_elapsed_soft_tranq10_09_20260606.csv`
  with `journey_certificate_completion_bound_elapsed_soft_return_enabled=false`.
- Result remained root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=119.192375`, `nodes=1`, `columns=527`.
- The first CB call grew from about `18s` to `25.9s`, candidates grew from
  `97` to `211`, and selected columns grew from `15` to `20`; however all
  selected columns were replacement-only and no certificate was reached.

- Probe with larger CB harvest:
  `BPC_future/results/probe_cb_harvest64_tranq10_09_20260606.csv`
  using `max_returned=64`, `min_journeys=40`, `min_fill=40`,
  and `soft_return_min_journeys=40`.
- Result remained root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=119.217539`, `nodes=1`, `columns=542`.
- It selected only `17` CB columns in the first expensive retry, again all
  replacement-only.  Later ordinary exact/profile found additional new task-set
  directions, but still not enough to prove the node.

Decision:

- Do not disable elapsed soft return by default.
- Do not increase CB harvest size in the 5/10/20 mainline configs by default.
  Both variants spend more tail budget and mostly add replacement columns
  without reaching a certificate.
- The missing piece is not just "return later" or "return more"; it is stronger
  direct-label proof/search quality before replacement-only tail batches consume
  the remaining budget.

## 2026-06-06: Larger Profile Worker Batch

Context:

- Early/mid ordinary profile pricing is expensive on `tranq10_09`, with several
  calls returning around `48` columns after seconds of profile generation.
  Hypothesis: larger worker batches might reduce CG iterations and leave more
  time for the final judge.

Tested behavior:

- Probe:
  `BPC_future/results/probe_profile_batch96_tranq10_09_20260606.csv`.
- Temporary overrides:
  `journey_pricing_late_max_returned_journeys=128`,
  `journey_pricing_late_early_return_negative_min_count=96`,
  `journey_pricing_late_streaming_min_negative_batch=96`.
- Result remained root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=118.263699`, `nodes=1`, `columns=625`.
- Exact/profile time dropped from roughly `69s` to `52s`, but the run needed
  more tail work: `exact_completion_bound_retry=3`, about `38s` of CB time, and
  far more columns.  The objective stayed flat at the same value.

Decision:

- Do not raise profile worker batch sizes by default.  It shifts work from
  profile generation into a larger degenerate tail and increases RMP volume.
- If revisited, pair larger batches with a demonstrably stronger tail proof
  mechanism; larger batches alone do not solve the hard case.

## 2026-06-06: Tail Dual Averaging Worker

Context:

- The hard `tranq10_09` tail has flat objective rounds with large dual motion,
  so historical dual averaging was tested as a worker-only dual center.  The
  implementation keeps exactness by true-RC filtering every column found under
  the averaged dual and falling back to true-dual pricing for certificate.

Tested behavior:

- Probe:
  `BPC_future/results/probe_dual_avg_tranq10_09_20260606.csv`.
- Temporary override:
  `journey_dual_averaging_enabled=true`.
- Result remained root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=120.057128`, `nodes=1`, `columns=528`.
- Dual averaging activated once at `cg_iter=12` after three flat rounds
  (`cover_l1_delta=13.133436982`, `cover_linf_delta=4.421656476`).
- Under averaged duals, profile DP found negative objective structure
  (`best_average_reduced_cost=-4.391415676`,
  `profile_negative_candidate_count=135`), but all candidates were unusable:
  `duplicate_candidates_filtered=13`,
  `dominated_task_set_journeys_filtered=161`,
  and `kept_journeys=0` after true-RC filtering.  The averaging worker then
  entered cooldown until `cg_iter=22`.

Decision:

- Do not enable `journey_dual_averaging_enabled` by default in the main
  5/10/20 configs.  It did not produce true-RC addable columns on the current
  hard case.
- Keep the implementation and logs as an opt-in diagnostic.  If revisited, it
  needs a better use than ordinary profile candidate generation, for example
  ranking direct-label task-set exploration while still applying true-RC
  filtering.

## 2026-06-06: Hidden Patrol Journey-Level K=10 Beam

Context:

- `direct_journey_label_max_labels_per_node` was intended to bound both sortie
  partial labels and direct journey labels in worker-only beam patrols.
- The helper `_add_direct_journey_label` already supported the cap, but the
  direct journey loop did not pass the configured value, so the journey-level
  cap was not active.  This was fixed and covered by a unit test.

Tested behavior:

- Probe:
  `BPC_future/results/probe_hidden_patrol_k10_journeycap_tranq10_09_20260606.csv`.
- Temporary override:
  `journey_hidden_negative_patrol_max_labels_per_node=10`.
- Result remained root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=119.351001`, `nodes=1`, `columns=532`.
- Aggregate pricing shape stayed near the previous hard-case baseline:
  `18` ordinary exact/profile calls with about `67.28s` profile generation,
  `5` hidden patrol calls with about `2.78s`, and `2` completion-bound retries
  with about `28.20s`.
- The hidden patrol did find a few candidates at `cg_iter=11-13`, but later
  still returned no candidate at `cg_iter=15` and `18`; the completion-bound
  judge still had to return replacement-heavy batches.

Decision:

- Keep the code fix because it makes the worker cap real and protects memory in
  opt-in beam patrols.
- Do not enable `journey_hidden_negative_patrol_max_labels_per_node=10` by
  default in the 10/20 mainline configs.  On the current hard case it is not a
  performance breakthrough.
- If revisited, pair the cap with a new ordering or task-set exploration rule;
  K-beam alone still misses the proof-tail structure.

## 2026-06-06: Two-Cycle Return-Ready Future Suffix

Context:

- The two-cycle completion-bound table previously handled "return to depot,
  then future sorties" by adding `future_sortie_floor * future_sorties`.
- That is exact-safe but very loose because it ignores the actual depot ready
  time after returning and recharging from the current sortie.
- The bound was tightened so each return candidate carries its depot ready
  time, then the first future sortie lower bound is queried from the depot time
  bucket at that ready time.  Additional future sorties still use the global
  floor, keeping the value optimistic.

Tested behavior:

- Probe:
  `BPC_future/results/probe_twocycle_return_suffix_tranq10_09_20260606.csv`.
- Result remained root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=118.179748`, `nodes=1`, `columns=530`.
- Aggregate pricing remained close to the current hard-case baseline:
  `17` ordinary exact/profile calls with about `67.98s`, `5` hidden patrol
  calls with about `2.79s`, and `2` completion-bound retries with about
  `26.77s`.
- The first completion-bound retry was effectively unchanged:
  `97` candidate negatives, `15` selected replacement-only journeys, and
  `202,843` bound-pruned labels.

Decision:

- Keep the code because it is a strictly tighter optimistic return-suffix bound
  and has unit coverage for the return-ready-time behavior.
- Do not treat it as a standalone performance breakthrough for the hard
  `tranq10_09` tail.  The main bottleneck remains repeated ordinary
  exact/profile work and replacement-heavy final-judge batches.

## 2026-06-06: Streaming Physical Catalog Hit Logging

Context:

- Hard-case logs showed `profile_catalog_hit=False` on every ordinary
  exact/profile call, while `label_physical_catalog=True` and
  `label_resume_profiles` kept growing from `5,000` toward the exhausted
  physical catalog.  This made it look like the worker was rebuilding the
  physical catalog from scratch each CG round.

Fix:

- Streaming profile-pricing result constructors now propagate
  `catalog_stats["hit"]` and `catalog_stats["size"]` into
  `profile_catalog_hit` and `profile_catalog_size`.
- Added a regression test showing the first streaming physical-catalog call is
  a miss and the second call with the same cache reports a hit.

Validation:

- Targeted tests:
  `test_streaming_label_physical_catalog_returns_true_negative_journey`,
  `test_streaming_label_physical_catalog_reports_cache_hit_on_reuse`, and
  `test_streaming_partial_result_records_callback_times` all passed.
- A 30-second `tranq10_09` probe confirmed the corrected log semantics:
  `cg_iter=2` reported `profile_catalog_hit=False`, then `cg_iter>=3` reported
  `profile_catalog_hit=True` while the physical catalog incrementally grew.

Decision:

- Do not interpret older streaming `profile_catalog_hit=False` logs as evidence
  that physical catalog resume was disabled.  Use `label_physical_catalog`,
  `label_resume_profiles`, and the corrected `profile_catalog_hit` together.
- This is a semantics/audit fix, not a performance breakthrough.  The hard-case
  bottleneck remains catalog expansion and profile-DP scanning, not a missing
  cache.

## 2026-06-06: Profile Materialization Failure Retry Bypass

Context:

- A profile worker can return `selected_profiles_not_a_valid_journey`: it found
  a negative profile combination, but materialization did not yield a valid
  journey.
- Skipping the following ordinary exact/profile retry and going directly to the
  completion-bound final judge is exact-safe in isolation, because the result
  remains uncertified unless the true-dual judge proves no negative column.
- The proposed benefit was to avoid repeating the same invalid profile choice.

Tested behavior:

- Probe with bypass enabled and the current `6s` after-retry CB minimum:
  `BPC_future/results/probe_retry_bypass2_120_tranq10_09_20260606.csv`.
  Result stayed root `TIME_LIMIT`, `solving_time=118.617685`, `columns=496`.
  It logged one retry skip, removed the ordinary retry, but triggered more
  completion-bound retry work and still failed to certify.
- Probe with bypass enabled and
  `journey_certificate_completion_bound_after_retry_min_time=10.0`:
  `BPC_future/results/probe_retry_bypass_min10_120_tranq10_09_20260606.csv`.
  Result stayed root `TIME_LIMIT`, `solving_time=119.263616`, `columns=496`.
  It reduced total pricing calls but did not improve proof or incumbent quality.
- The better comparison point remains the min-6 no-bypass probe:
  `BPC_future/results/probe_cb_min6_120_tranq10_09_20260606.csv`, which also
  timed out but finished the run loop sooner at about `116.1s` and kept more
  columns (`506`).

Decision:

- Keep the bypass implementation as an explicit diagnostic switch only.
- Do not enable
  `journey_skip_ordinary_retry_after_profile_materialization_failure` by
  default.  The default is `False`.
- If revisited, pair it with a better final-judge saturation rule or worker
  repair mechanism.  Bypassing the retry alone just shifts work between worker
  and judge without fixing the root hidden-negative/certificate tail.

## 2026-06-06: Profile Materialization Feasibility Filter

Context:

- A profile-DP selected candidate can later fail to become an accepted journey.
  One hypothesis was that the selected physical profiles were impossible to
  materialize into a feasible timed journey, so pre-filtering candidates with an
  instantiation check might avoid repeated invalid selections.
- The implementation was exact-safe as a worker repair: it only skips a profile
  candidate before returning worker columns, and the no-column outcome remains
  uncertified unless the true-dual direct-label judge proves it.

Tested behavior:

- Probe with the feasibility filter enabled:
  `BPC_future/results/probe_profile_materialization_filter_120_tranq10_09_20260606.csv`.
  Result stayed root `TIME_LIMIT`, `solving_time=118.071644`, `columns=506`.
- The comparison min-6 no-filter probe
  `BPC_future/results/probe_cb_min6_120_tranq10_09_20260606.csv` also timed
  out but finished the loop earlier at about `116.1s` with the same column
  count.
- The filter counter stayed at zero on the hard-case `cg_iter=12` and
  `cg_iter=28` events, while the selected-candidate failure still appeared.
  That indicates the current failure was not a missing physical materialization
  precheck.  It was more consistent with a profile-DP negative candidate becoming
  nonnegative under manual true-RC accounting.

Decision:

- Keep `profile_materialization_feasibility_filter_enabled` default `False`.
- Use it only as a diagnostic switch when logs specifically show physical
  materialization infeasibility.
- Keep the separate log-semantics fix that counts manual true-RC filtered
  profile candidates as `weak_negative_journeys_filtered`; that improves the
  hidden-negative audit without changing the worker universe.

## 2026-06-06: Hidden Patrol Final-Reserve Gate

Context:

- In hard 10-task tail rounds, hidden-negative patrol can consume the last
  fraction of the final-judge budget.  A proposed fix was to set
  `journey_hidden_negative_patrol_final_reserve_time` equal to the completion
  bound proof budget, so the patrol would not run when the final judge was close
  to its minimum time.

Tested behavior:

- Probe:
  `BPC_future/results/probe_patrol_reserve_120_tranq10_09_20260606.csv`.
  Result stayed root `TIME_LIMIT`, `solving_time=118.329728`, `columns=496`.
- The reserve gate changed the tail behavior: at `cg_iter=27`, the solver went
  directly to completion-bound retry with `remaining=7.836091` instead of
  running the 0.5s hidden patrol.
- This skipped the true-dual hidden patrol column that the previous probe found
  at the same stage (`best_reduced_cost=-2.673127`).  The completion-bound final
  judge still timed out after `bound_build_time=2.267678` and about `6.10s` of
  search, without certifying the node.

Decision:

- Do not enable `journey_hidden_negative_patrol_final_reserve_time` in the
  5/10/20 main configs.
- The final seconds are not just wasted patrol time: the patrol can still find
  real hidden negatives.  The better fix is to find those hidden negatives
  earlier or make the final judge cheaper, not to suppress the worker solely to
  preserve a still-insufficient proof window.

## 2026-06-06: Evidence-Gated Pre-Exact Hidden Patrol

Context:

- A broad flatness-only pre-exact hidden-negative patrol had already failed.
  The implementation was later tightened so pre-exact patrol only runs after a
  previous local no-column result was followed by a true-dual hidden negative.
- This stricter trigger looked like a plausible way to avoid repeated
  ordinary exact/profile scans in the hard root tail without making patrol a
  certificate oracle.

Tested behavior:

- Probe:
  `BPC_future/results/probe_preexact_evidence_patrol_120_tranq10_09_20260606.csv`.
- Temporary override:
  `journey_hidden_negative_patrol_before_exact_flat_enabled=True`.
- Result remained root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=114.480953`, `nodes=1`,
  `columns=498`.
- The stricter pre-exact patrol triggered `4` times.  It found some true-dual
  negative columns at `cg_iter=24` and `cg_iter=25`, but still left later
  ordinary exact/profile and hidden patrol calls to run.
- Total work remained large: `pricing_calls=59`, `exact_pricing_calls=31`,
  `generated_sequences=2,051,610`, and
  `evaluated_timed_trips=2,486,910`.

Decision:

- Keep `journey_hidden_negative_patrol_before_exact_flat_enabled` disabled in
  the 5/10/20 main configs.
- The stricter trigger is safer than broad flatness triggering, but it still
  does not repair the hard `tranq10_09` certificate tail.
- Revisit only if paired with a stronger rule for when patrol discoveries
  suppress or reshape the following profile-DP scan; running it as an extra
  worker alone increases control-flow churn.

## 2026-06-06: 10-Task NG/DSSR Flag-Only Probe

Context:

- The 20-task smoke config enables direct-label NG/DSSR knobs, while the
  current 10-task config does not.  Since the hard 10-task tail still has
  hidden-negative behavior, a probe tried enabling the same NG/DSSR flags in
  the 10-task config.

Tested behavior:

- Probe:
  `BPC_future/results/probe_ng_frontend_120_tranq10_09_20260606.csv`.
- Temporary overrides enabled
  `journey_pricing_direct_journey_label_ng_dssr_enabled=True` with memory size
  `6`, probe time `4.0`, and no remaining-time disable gate.
- Result remained root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=114.653884`, `nodes=1`,
  `columns=496`.
- Logs showed `direct_journey_label_ng_dssr_enabled=True` on exact pricing
  rows, but `ng_dssr_iterations=0` and `ng_memory_size=0`; the run still used
  the cached profile-DP path rather than an NG direct-label front-end.

Decision:

- Do not treat flag-only NG/DSSR enablement as a tested improvement.
- Do not copy the 20-task NG settings into the 10-task default unless the
  dispatch path is also changed and verified to actually execute NG/DSSR.
- The current hard-case bottleneck remains repeated profile-DP scans and
  late hidden-negative/final-judge work, not a missing YAML flag by itself.

## 2026-06-06: Completion-Bound Suffix-Only Cache Tradeoff

Context:

- Direct-label completion-bound final probes disable the next-sortie cache when
  partial pruning is enabled, because partial pruning is parent-label
  dependent.
- A possible exact-safe tradeoff is to disable partial pruning but enable the
  next-sortie cache, keeping only suffix-level completion pruning.  Disabling
  pruning can only make the bound looser, not invalid.

Tested behavior:

- Probe:
  `BPC_future/results/probe_cb_suffix_cache_120_tranq10_09_20260606.csv`.
- Temporary overrides:
  `journey_certificate_completion_bound_partial_pruning_enabled=False` and
  `journey_pricing_direct_journey_label_next_sortie_cache_enabled=True`.
- Result remained root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=114.587028`, `nodes=1`,
  `columns=496`.
- In this run the final completion-bound judge still did not get enough budget
  to run meaningfully; the tail remained dominated by ordinary profile-DP and
  hidden patrol work.

Decision:

- Do not switch the mainline to suffix-only completion-bound caching by
  default.
- If revisited, test it in a state where the completion-bound final judge
  actually runs with enough budget; this probe mostly shows that the scheduling
  bottleneck is upstream of the final direct-label search.

## 2026-06-06: Completion-Bound Time/Energy Buckets 15/15

Context:

- The two-cycle completion-bound table can be tightened by increasing the
  resource bucket count from the default `10/10` to `15/15`.
- The hope was that a tighter suffix lower bound would prune more direct-label
  states in the hard 10-task proof tail.

Tested behavior:

- Probe:
  `BPC_future/results/probe_cb_buckets15_120_tranq10_09_20260606.csv`.
- Temporary overrides:
  `journey_certificate_completion_bound_time_buckets=15`,
  `journey_certificate_completion_bound_energy_buckets=15`, and
  `journey_certificate_completion_bound_two_cycle_max_states=600000`.
- Result stayed root `TIME_LIMIT`, `solving_time=119.085068`, `columns=495`.
- The first completion-bound table grew from roughly `83,853` states to
  `177,408` states, and bound construction time grew from about `2.2s` to
  about `4.7s`.  The extra pruning was not enough to pay for the larger table.

Decision:

- Do not enable `15/15` buckets by default.
- Keep `10/10` as the current practical default until a more targeted
  resource-aware bound improves pruning without doubling table size and build
  time.

## 2026-06-06: Duplicate-Saturation Soft Return At 5s

Context:

- Completion-bound harvesting sometimes becomes duplicate-task-set saturated:
  it has many true-RC negative physical candidates but only a small number of
  unique RMP task-set directions.
- A separate duplicate-saturation soft-return threshold was added as an opt-in
  control so that this condition can return earlier than the generic
  `journey_certificate_completion_bound_diverse_harvest_soft_return_after_time`.
- Exactness is preserved because it only returns true-RC negative columns; it
  never certifies no-negative-column status.

Tested behavior:

- Probe:
  `BPC_future/results/probe_duplicate_saturation5_120_tranq10_09_20260606.csv`.
- Temporary default-style setting:
  `journey_certificate_completion_bound_diverse_harvest_duplicate_saturation_after_time=5.0`.
- Result stayed root `TIME_LIMIT`, `solving_time=119.527037`, `columns=490`.
- Compared with the no-bypass/min-6 baseline
  `BPC_future/results/probe_cb_min6_120_tranq10_09_20260606.csv`, the 5s
  duplicate-saturation probe had fewer columns (`490` vs `506`), more generated
  sequences (`2.04M` vs `1.54M`), more evaluated timed trips (`2.46M` vs
  `1.91M`), and more completion-bound retry pricing events (`4` vs `2`).

Decision:

- Keep the duplicate-saturation soft-return code as an explicit opt-in tuning
  hook.
- Do not set
  `journey_certificate_completion_bound_diverse_harvest_duplicate_saturation_after_time=5.0`
  in the main 5/10/20 configs.  Returning that early creates more tail rounds
  and shifts work back to ordinary exact/profile pricing.

## 2026-06-06: Late Bounded Profile True-RC Materialization

Context:

- Hidden-negative audit showed that hard 10-task hidden negatives were often
  inside the profile/reachable/all-trip mask universe, but were not selected as
  true-RC negative worker columns.
- A bounded opt-in materialization window was added so late profile/exact calls
  can scan more rough-objective candidates by true reduced cost without making
  profile no-column a certificate.

Tested behavior:

- Probe:
  `BPC_future/results/probe_late_materialization_cap96_tranq10_09_20260606.csv`.
- Temporary overrides:
  `journey_pricing_late_profile_true_rc_materialization_slack=3.0` and
  `journey_pricing_late_profile_true_rc_materialization_max_candidates=96`.
- Result remained root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=119.252946`, `columns=510`.
- Pricing calls dropped from the recent hard-case baseline level to `47`, and
  profile DP time fell to about `13.84s`, so the cap did execute and compressed
  some profile-DP scanning.
- The run still timed out, grew the RMP matrix, and completion-bound retry work
  increased to about `30.86s`.  Hidden-negative audit summaries shifted toward
  duplicate/dominated/weak materialization churn rather than genuinely wider
  RMP directions.

Decision:

- Keep the bounded materialization code path as explicit opt-in diagnostic
  infrastructure.
- Do not enable late slack/cap materialization in the main 5/10/20 configs.
  The current evidence says it moves work from profile-DP search into
  duplicate/dominated true-RC materialization and a larger final-judge tail,
  rather than fixing the certificate bottleneck.

## 2026-06-06: Duplicate-Only Ordinary Retry Skip

Context:

- Profile workers can return `negative_journeys_already_in_pool`: the local
  worker saw negative-looking candidates, but every selected candidate was
  already present, forbidden, weak, or dominated by an existing task-set column.
- A narrow opt-in scheduler helper was added so this case can skip the ordinary
  profile retry and go directly to the true-dual final judge.  The helper does
  not create a certificate; it only changes which exact-safe oracle runs next.

Tested behavior:

- Probe:
  `BPC_future/results/probe_duplicate_skip_tranq10_09_20260606.csv`.
- Temporary mainline-style setting:
  `journey_skip_ordinary_retry_after_duplicate_only=True`.
- Result stayed root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=118.71258`, `columns=496`.
- The skip did not trigger on the hard path.  The run still had `58` pricing
  calls, including `23` ordinary exact/profile calls, `4` hidden-negative
  patrol calls, and `2` completion-bound retries.  Ordinary exact/profile still
  spent about `67.37s` in profile generation and `19.28s` in profile DP.

Decision:

- Keep the code and unit coverage as an opt-in protection for future
  duplicate-only worker failures.
- Do not enable `journey_skip_ordinary_retry_after_duplicate_only` in the main
  5/10/20 configs by default.  It does not address the current hard
  `tranq10_09` bottleneck, which remains physical catalog expansion plus
  repeated local profile-DP worker rounds.

## 2026-06-06: Streaming Callback Exhaust After Large Physical Catalog

Context:

- The hard `tranq10_09` logs showed expensive late physical-catalog streaming
  growth.  A narrow opt-in switch,
  `journey_pricing_streaming_callback_exhaust_after_profile_count`, was added
  to stop intermediate streaming callbacks once the dual-independent physical
  catalog already contains enough profiles.  After the threshold, the catalog
  generator keeps expanding and the caller runs one final DP over the returned
  catalog.
- This is exact-safe as worker scheduling only: it does not change reduced-cost
  formulas, does not make profile no-column a certificate, and defaults to `0`
  (disabled).

Tested behavior:

- Probe:
  `BPC_future/results/probe_stream_exhaust_after25k_tranq10_09_20260606.csv`.
- Override:
  `journey_pricing_streaming_callback_exhaust_after_profile_count=25000`.
- Result stayed root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=119.076096`, `primal=203.102839`,
  `columns=490`.
- The new gate triggered twice.  The large late calls shifted work into longer
  catalog expansion instead of closing the instance:
  `cg7` profile generation was about `22.87s` at `33393` profiles and `cg8`
  was about `17.85s` at `36676` profiles.
- Aggregate pricing still had `42` pricing calls, including costly true-dual
  exact/profile work and two completion-bound retry events.  The hard case
  remained a root certificate miss.

Decision:

- Keep the switch as opt-in diagnostic infrastructure and for future bounded
  worker scheduling probes.
- Do not enable
  `journey_pricing_streaming_callback_exhaust_after_profile_count=25000` in the
  main 5/10/20 configs.  Exhausting after a large catalog did not reduce the
  current hard-tail bottleneck; it mostly moved cost from repeated callbacks
  into fewer but longer catalog-expansion calls.

## 2026-06-06: No-Negative-Only Profile True-RC Materialization

Context:

- Hidden-negative audit showed rounds where ordinary profile DP had no rough
  negative candidates, but the same task masks later appeared as true-dual
  direct-label hidden negatives.  A narrower opt-in materialization window was
  added:
  `journey_pricing_profile_no_negative_true_rc_materialization_slack` and
  `journey_pricing_profile_no_negative_true_rc_materialization_max_candidates`.
- Unlike the earlier global materialization slack, this window is only used
  when profile DP has zero rough-negative candidates.  It is a worker repair
  mechanism only, not a certificate path, and defaults to disabled.

Tested behavior:

- Probe:
  `BPC_future/results/probe_no_negative_materialization_tranq10_09_20260606.csv`.
- Overrides:
  `journey_pricing_late_profile_no_negative_true_rc_materialization_slack=1.5`
  and
  `journey_pricing_late_profile_no_negative_true_rc_materialization_max_candidates=48`.
- Result stayed root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=119.435642`, `primal=203.102839`,
  `columns=510`.
- The new window did trigger, but the selected no-negative materialization
  candidates mostly became weak true-RC or dominated/replacement candidates.
  Examples from the probe include heuristic rows with
  `profile_no_negative_materialization_selected_candidate_count > 0` and
  `weak_negative_journeys_filtered > 0`, and exact rows where dozens of
  no-negative candidates were capped but not scanned because ordinary rough
  negative candidates already existed.
- The run increased the RMP column count and still needed completion-bound
  retries; it did not reduce the root certificate tail.

Decision:

- Keep the no-negative-only materialization code as an opt-in diagnostic/repair
  hook because it is narrower and safer than the old global slack.
- Do not enable the late no-negative materialization window in the main 5/10/20
  configs.  Current evidence says the near-zero profile candidates are mostly
  weak or dominated under true RC, not the missing high-value worker columns.

## 2026-06-06: Wider Profile True-RC Candidate Scan

Context:

- A narrow opt-in scan-width control was added:
  `journey_pricing_profile_true_rc_candidate_scan_factor` and
  `journey_pricing_profile_true_rc_candidate_scan_max_candidates`.
- The intent was to decouple the number of rough profile-DP candidates rescored
  by true RC from `max_returned_journeys`, while leaving the final number of
  columns added to the RMP unchanged.
- This is worker-only and exact-safe: candidates still pass
  `manual_journey_reduced_cost`; profile no-column remains uncertified.

Tested behavior:

- Probe:
  `BPC_future/results/probe_profile_scan12_tranq10_09_20260606.csv`.
- Overrides:
  `journey_pricing_late_profile_true_rc_candidate_scan_factor=12` and
  `journey_pricing_late_profile_true_rc_candidate_scan_max_candidates=768`.
- Result stayed root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=118.772265`, `primal=203.102839`,
  `columns=496`.
- Aggregate logs showed the effective selected rough profile candidates still
  peaked at `48`.  The wider scan did not materialize because profile DP
  early-return logic still stopped after the configured late negative batch.
- Hidden-negative audit still showed direct-label/completion-bound hidden
  negatives after ordinary/profile local no-column or weak true-RC filtering.

Decision:

- Keep the scan-width control as opt-in infrastructure.
- Do not enable it in the main configs as a standalone fix.  On the current
  hard case it did not reach the intended wider true-RC rescoring stage; the
  blocker is earlier profile-worker early return / representation, not just
  candidate scan width.

## 2026-06-06: Replacement-Only Profile Materialization

Context:

- Hidden-negative audit on `tranq10_09` showed many CB-found columns were
  same-task-set replacement columns: `dominant_task_set_cost_delta` matched the
  CB true reduced cost.  This indicated a lower physical route for an existing
  task set, not a new task-set direction.
- A narrower replacement-only materialization window was added:
  `journey_pricing_profile_replacement_true_rc_materialization_slack` and
  `journey_pricing_profile_replacement_true_rc_materialization_max_candidates`.
- A near-zero candidate is scanned only if its profile-level task-set cost is
  lower than the current dominant cost for the same task mask.  It still must
  pass true-RC filtering before entering the RMP.

Tested behavior:

- Probe:
  `BPC_future/results/probe_replacement_materialization_tranq10_09_20260606.csv`.
- Overrides:
  `journey_pricing_late_profile_replacement_true_rc_materialization_slack=2.0`
  and
  `journey_pricing_late_profile_replacement_true_rc_materialization_max_candidates=64`.
- Result stayed root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=119.251751`, `primal=203.102839`,
  `columns=510`.
- The replacement window did trigger: pricing logs aggregated
  `108` replacement candidates scanned and `108` selected for true-RC
  materialization.  However hidden-negative audit still had
  `worker_true_rc_threshold_filter` as the primary miss reason.
- For the first hidden negative, the ordinary profile universe had the hidden
  task mask (`ordinary_hidden_task_mask_profile_hit=True`), but the selected
  profile candidates did not include it
  (`ordinary_hidden_task_mask_selected_hit=False`).  The replacement candidates
  selected by the worker were not the CB-found lower-cost physical path for
  mask `395`.

Decision:

- Keep replacement-only materialization as opt-in diagnostic/repair code.
- Do not enable it in the main configs yet.  The hard-case miss is now more
  likely a profile-representation / physical-path representative issue, so the
  next performance focus should shift toward direct-label patrol/final-judge
  batching and trigger control rather than more profile materialization knobs.

## 2026-06-06: Root Replacement Repair Before Completion-Bound Judge

Context:

- A proof-safe Level 2.5 repair hook was inserted after ordinary exact retry
  and before completion-bound final judge.
- The hook uses true RMP duals, disables profile pricing, enables direct-label
  existing-task-set repair only, and is never certificate-capable.  Its only
  purpose is to catch hidden replacement columns cheaply before invoking the
  heavier completion-bound judge.

Tested behavior:

- Probe:
  `BPC_future/results/probe_root_replacement_repair_tranq10_09_20260606.csv`.
- Override:
  `journey_replacement_repair_enabled=true`.
- Result stayed root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=119.206248`, `primal=203.102839`,
  `columns=501`.
- The hook now reached the intended path: logs showed
  `journey_replacement_repair=2` and
  `pricing_kind=exact_replacement_repair=2`.
- Both repair calls failed to produce columns:
  `pricing_state=INCOMPLETE_LIMIT`, `reason=timed_trip_pricing_incomplete`,
  `negative_journeys=0`.
- Completion-bound retry was still needed twice.  Those two calls found hidden
  negatives with harvesting stats:
  first `harvest_candidate_negative_count=102`, `harvest_selected_count=12`,
  `harvest_selected_new_task_set_count=1`,
  `harvest_selected_replacement_task_set_count=11`; second
  `harvest_candidate_negative_count=78`, `harvest_selected_count=4`,
  `harvest_selected_new_task_set_count=0`,
  `harvest_selected_replacement_task_set_count=4`.
- Hidden-negative primary reasons remained dominated by
  `worker_profile_universe_missing_hidden_task_set` in the completion-bound
  retries, while one patrol case showed `profile_cross_count_dominance`.

Decision:

- Keep the root repair hook available as opt-in infrastructure, because it now
  has the correct funnel position and exact-safe semantics.
- Do not enable it as a mainline performance fix yet.  On the current hard case
  it triggers but times out before finding columns, so the next priority remains
  final-judge harvesting breadth and worker universe repair rather than another
  narrow replacement-only patrol knob.

## 2026-06-06: Completion-Bound Soft Return Minimum New Task Set Gate

Context:

- Completion-bound diverse harvesting sometimes returned replacement-heavy
  batches through elapsed soft return.  A guarded opt-in was added:
  `journey_certificate_completion_bound_diverse_harvest_soft_return_min_new_task_sets`.
- The gate only blocks elapsed/duplicate-saturation soft return until the
  selected harvested batch contains at least the configured number of new
  task-set directions.  It still allows remaining-time soft return, so it does
  not affect exactness or force unbounded tail search.

Tested behavior:

- Probe:
  `BPC_future/results/probe_cb_min_new_taskset_tranq10_09_20260606.csv`.
- Temporary mainline-style setting:
  `journey_certificate_completion_bound_diverse_harvest_soft_return_min_new_task_sets=1`
  in the 10-task config.
- Result stayed root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=118.996987`, `primal=203.102839`,
  `columns=496`.
- The first completion-bound retry already had one selected new task-set, so
  the new gate did not delay its elapsed soft return:
  `harvest_candidate_negative_count=152`, `harvest_selected_count=17`,
  `harvest_selected_new_task_set_count=1`,
  `harvest_selected_replacement_task_set_count=16`.
- A later completion-bound retry near the wall-clock limit ran with only about
  `6s` and ended `INCOMPLETE_LIMIT/time_limit` without returning columns.

Decision:

- Keep the code-level gate and tests as opt-in instrumentation for future
  experiments.
- Do not enable it in the 5/10/20 mainline configs by default.  On the current
  hard case, requiring at least one new task-set before elapsed soft return did
  not solve the replacement-heavy tail and can push a later final judge into a
  short-budget timeout.

## 2026-06-06: Hidden Patrol Before After-Retry Completion-Bound Judge

Context:

- The branch-price main loop already used hidden-negative patrol after local
  profile no-column, but the after-retry path could still go directly from
  `INCOMPLETE_LIMIT/weak_negative_journeys_filtered` to the completion-bound
  final judge.
- A root/branch-consistent patrol was inserted immediately before the
  after-retry completion-bound judge.  It uses true RMP duals, is not
  certificate-capable, and keeps the existing `journey_hidden_negative_patrol_*`
  budgets.

Tested behavior:

- Probe:
  `BPC_future/results/probe_after_retry_patrol2_tranq10_09_20260606.csv`.
- Result stayed root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=119.195376`, `primal=203.102839`,
  `columns=490`.
- The new hook did reach the intended branch-price path:
  `journey_hidden_negative_patrol_after_retry=1`.
- It found two true-dual negative replacement columns in about `0.5s` at
  `cg_iter=13`, with `harvest_selected_new_task_set_count=0` and
  `harvest_selected_replacement_task_set_count=2`.
- Completion-bound retry calls dropped to one in this probe, but the remaining
  CB call at `cg_iter=22` was still expensive and replacement-only:
  `harvest_candidate_negative_count=96`, `harvest_selected_count=12`,
  `harvest_selected_new_task_set_count=0`,
  `harvest_selected_replacement_task_set_count=12`.
- 5-task smoke after the change remained exact:
  `probe_after_retry_patrol_tasks5_20260606.csv` solved both 5-task instances
  to `OPTIMAL` in `2.289745s` and `1.554308s`.

Decision:

- Keep the after-retry patrol hook as a healthy funnel improvement.  It can
  replace an early expensive CB worker call with a bounded 0.5s true-dual
  patrol and did not break 5-task exactness.
- Do not treat it as the final hard-tail solution.  The hard 10-task instance
  still timed out, and the remaining blocker is still replacement-heavy tail
  degeneracy plus insufficient genuinely new task-set directions.

## 2026-06-06: Late Streaming Minimum True-Returned Columns

Context:

- Hard-tail logs showed that streaming/profile pricing can stop after finding
  only one or two true-RC usable journeys even when rough profile-DP has many
  negative candidates.  A late-stage control was added:
  `journey_pricing_late_streaming_min_returned_journeys`.
- The control is worker-only.  It changes when a streaming callback returns
  negative columns, but no profile no-column result becomes a certificate.

Tested behavior:

- Probe:
  `BPC_future/results/probe_late_min_returned4_tranq10_09_20260606.csv`.
- Temporary override:
  `journey_pricing_late_streaming_min_returned_journeys=4`.
- Result stayed root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=118.161833`, `primal=203.102839`,
  `columns=485`.
- The gate changed the tail path but did not solve it.  It forced some ordinary
  exact/profile calls to return at least four columns (`cg_iter=10-11`), but a
  weak true-RC filtered round still triggered after-retry patrol and then an
  early completion-bound retry at `cg_iter=13`.
- That completion-bound retry harvested `15` journeys, but `14` were
  replacement task sets and only `1` was a new task-set direction.  A later
  final judge still timed out near `cg_iter=24`.

Decision:

- Keep the mapping and test coverage as an opt-in diagnostic/worker cadence
  control.
- Do not enable it by default in the 5/10/20 configs.  Static minimum
  true-returned columns can move completion-bound calls earlier, but it does
  not address the root hard-tail issue: the remaining negative columns are
  replacement-heavy and do not reshape the degenerate RMP fast enough.

## 2026-06-06: Completion-Bound After Small Exact Batch

Context:

- The hard `tranq10_09` tail has many objective-flat rounds where ordinary
  true-dual exact/profile pricing returns only one to three journeys.  A narrow
  experiment tried invoking the completion-bound direct-label oracle
  immediately after such a small batch, before the next RMP solve, to harvest a
  broader set of true-RC columns while enough wall-clock remained.
- This was tested as a worker-only supplement.  A no-column result from this
  supplement would not be a certificate because the same round had already
  added negative columns, invalidating the current dual for the expanded RMP.

Tested behavior:

- Probe:
  `BPC_future/results/probe_cb_after_small_batch_tranq10_09_20260606.csv`.
- Temporary overrides:
  `journey_certificate_completion_bound_after_small_batch_enabled=true`,
  `journey_certificate_completion_bound_after_small_batch_min_flat_rounds=2`,
  `journey_certificate_completion_bound_after_small_batch_max_added_journeys=3`,
  and
  `journey_certificate_completion_bound_after_small_batch_min_remaining_time=25.0`.
- Result stayed root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=119.119546`, `primal=203.102839`,
  `columns=497`.
- The supplement triggered at `cg_iter=12` with about `46.6s` remaining and
  spent about `15.1s`, but harvested `16` replacement task-set columns and
  `0` new task-set directions:
  `harvest_candidate_negative_count=149`,
  `harvest_selected_count=16`,
  `harvest_selected_new_task_set_count=0`,
  `harvest_selected_replacement_task_set_count=16`.
- A second probe also required at least one new task-set before elapsed soft
  return:
  `BPC_future/results/probe_cb_after_small_batch_minnew_tranq10_09_20260606.csv`.
  It also stayed root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=118.164085`, `columns=485`, and followed
  the same after-retry completion-bound pattern as the prior baseline.

Decision:

- Reverted the completion-bound-after-small-batch code path instead of keeping
  another disabled knob.  The evidence shows that pulling CB earlier in this
  way turns it into a replacement-heavy worker and does not reduce the final
  proof tail.
- Continue focusing on either stronger certificate pruning or a worker universe
  that produces genuinely new task-set directions, not more early CB calls.

## 2026-06-06: Official RMP Stabilized Duals In Certificate Pricing

Context:

- The solver already had an exact-safe `solve_journey_stabilized_dual` path:
  it solves an alternative optimal RMP dual LP, checks that its dual objective
  matches the RMP objective, and verifies all current pool columns have
  nonnegative reduced cost.
- A bug/limitation was found: `_journey_exact_pricing_duals` always switched
  completion-bound certificate pricing back to SCIP's extreme-point dual, even
  when `_select_journey_pricing_duals` had accepted an official stabilized
  dual.  This meant accepted stabilized duals were logged but not actually used
  by exact/certificate pricing.

Change:

- Allow `pricing_dual_source == "stabilized"` to pass into exact and
  completion-bound pricing as `stabilized_certificate`.
- This is exact-safe only because the stabilized dual source is emitted after
  current-pool feasibility and dual-objective checks.  GNN-smoothed and
  historical average duals remain excluded from certificate pricing.

Tested behavior:

- Probe 1:
  `BPC_future/results/probe_official_dual_stab_used_tranq10_09_20260606.csv`.
- Overrides:
  `journey_dual_stabilization_enabled=true`,
  `journey_dual_stabilization_tail_only_enabled=true`,
  `journey_dual_stabilization_certificate_candidate_enabled=true`,
  `journey_dual_stabilization_mode=slack_center`,
  and `journey_dual_stabilization_time_limit=0.5`.
- Stabilized duals were accepted and used:
  `pricing_dual_source=stabilized_certificate` appeared in exact/CB pricing.
- Result stayed root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=116.894847`, `columns=615`.
- `slack_center` produced extremely large negative reduced costs under the
  stabilized dual, for example `best_reduced_cost=-9390.30041725`, which
  inflated column volume without proving the node.

- Probe 2:
  `BPC_future/results/probe_official_dual_stab_l1_used_tranq10_09_20260606.csv`.
- Same setup but `journey_dual_stabilization_mode=l1_reference`.
- Result also stayed root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=119.073493`, `columns=473`.
- The completion-bound retry at `cg_iter=13` used
  `pricing_dual_source=stabilized_certificate`, ran about `41.7s`, and still
  harvested a replacement-heavy batch: `14` journeys, only `1` new task-set and
  `13` replacements.

Decision:

- Keep the exact-safe source-selection fix: if a future stabilized-dual policy
  is accepted by the RMP dual LP, exact/certificate pricing should be able to
  use it.
- Do not enable current stabilized-dual modes by default in the 5/10/20
  configs.  The tested policies either inflated columns (`slack_center`) or
  consumed too much certificate time without eliminating replacement-heavy
  tailing (`l1_reference`).
- If revisited, stabilized duals need additional regularization or bounds that
  avoid extreme dual rewards while preserving official current-pool
  feasibility.

## 2026-06-06: Flat Weak-Column Pressure Scheduling

Context:

- Hard 10-task tail logs showed many rounds where the RMP objective stayed at
  `203.102839` while pricing kept adding only a few true-RC negative journeys.
  Those columns are valid, but treating every small changed-column batch as full
  progress kept clearing certificate pressure and let learning/heuristic
  workers postpone the exact path by one RMP iteration at a time.

Change:

- Added an opt-in `journey_certificate_flat_weak_column_pressure_enabled`
  scheduler signal.
- It fires only for an incumbent-backed certificate candidate, after at least
  one flat RMP round, when the objective delta is within tolerance and the
  changed-column batch is small.
- In that case, learning/heuristic worker columns are still added, but the
  solver may continue to true-dual exact pricing in the same CG iteration
  instead of immediately re-solving the RMP.
- Exact/retry/repair paths now preserve existing proof pressure for such weak
  flat additions instead of always clearing it.
- This does not make worker no-column a certificate, does not use GNN duals for
  official proof, and does not change the final true-dual certificate rule.

Tested behavior:

- Hard probe:
  `BPC_future/results/probe_flat_weak_pressure_tranq10_09_20260606.csv`.
- Result stayed root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=117.354742`, `columns=495`,
  `primal=203.102839`.
- The new signal fired as intended.  For example, heuristic weak additions at
  `cg_iter=16`, `22`, and `23` continued into same-iteration exact pricing.
- The first completion-bound retry moved slightly earlier (`cg_iter=21` instead
  of the prior `cg_iter=22`), but it still selected only replacement task-set
  columns (`12` replacements, `0` new task sets).
- 5-task smoke remained exact and fast:
  `BPC_future/results/probe_flat_weak_pressure_tasks5_20260606.csv` solved the
  two configured 5-task instances to `OPTIMAL` in about `2.29s` and `1.56s`.

Decision:

- Keep the scheduler signal as a small proof-safe tail cleanup because it
  prevents weak learning/heuristic columns from blocking the exact layer for a
  full iteration.
- Do not treat it as the main breakthrough.  The hard-case bottleneck remains
  that exact/CB and hidden patrol mostly produce replacement-heavy columns or
  small batches that do not move the degenerate RMP objective.
- Next work should continue under the documented priority order, especially
  worker repair/new task-set directions and final-judge harvesting quality,
  rather than further tuning this flat weak-column threshold.

## 2026-06-06: Strict Min-New-Task-Set Gate For CB Return

Context:

- A hard 10-task probe showed completion-bound final judge returning a
  replacement-only batch: `direct_label_harvest_selected_count=18`,
  `direct_label_harvest_selected_new_task_set_count=0`,
  `direct_label_harvest_selected_replacement_task_set_count=18`.
- This happened even when
  `journey_certificate_completion_bound_diverse_harvest_soft_return_min_new_task_sets=1`
  was passed, because the ordinary direct-label early-return path was not
  gated by the min-new-task-set requirement.

Change:

- Tightened direct-label diverse harvesting so
  `direct_journey_label_diverse_harvest_soft_return_min_new_task_sets > 0`
  gates all incomplete-return paths:
  ordinary early return, elapsed/duplicate/remaining soft return, and the
  final incomplete selected-candidate return.
- This only blocks incomplete replacement-only batches.  If a true-dual final
  judge fully exhausts and finds replacement negative columns, they remain valid
  negative columns and must not be misreported as a no-column certificate.

Tested behavior:

- Probe:
  `BPC_future/results/probe_cb_min_new_gate_strict_tranq10_09_20260606.csv`.
- Result stayed root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=118.308861`, `columns=476`,
  `primal=203.102839`.
- The final CB retry still found replacement-only candidates:
  `direct_label_harvest_candidate_count=230`,
  `direct_label_harvest_selected_count=18`,
  `direct_label_harvest_selected_new_task_set_count=0`,
  `direct_label_harvest_selected_replacement_task_set_count=18`.
- Unlike the previous soft-return probe, those replacement-only candidates were
  not added back to the RMP.  The retry ended as `pricing_state=INCOMPLETE_LIMIT`
  and was rejected as a certificate.

Decision:

- Keep the semantic fix.  It makes the final judge less likely to become a
  replacement-column worker under an explicit min-new-task-set policy.
- Do not treat it as a speed improvement.  The hard case is now cleaner but
  still unresolved: ordinary/profile exact reaches only
  `LOCAL_NO_COLUMN_UNCERTIFIED`, hidden-negative patrol cannot prove or find a
  useful new task set, and completion-bound final judge cannot finish the global
  proof within the remaining budget.

## 2026-06-06: CB-Guided Replacement Repair Worker

Context:

- The earlier `Existing-Task-Set Replacement Repair Worker` failed before it
  could find the replacement-only columns later found by completion-bound
  direct-label pricing.
- A code audit found that `price_journeys()` only dispatched to direct-label
  pricing inside the profile frontend.  When replacement repair disabled
  `profile_pricing_enabled`, it fell through to the legacy timed-trip selection
  path instead of the intended direct-label path.

Change:

- Fixed `price_journeys()` so a direct-label-only config
  (`profile_pricing_enabled=False`, `direct_journey_label_pricing_enabled=True`)
  dispatches to direct-label / NG-DSSR directly.
- Added an opt-in
  `journey_replacement_repair_completion_bound_enabled` worker mode.  It uses
  completion-bound and optional two-cycle guidance inside replacement repair, but
  remains `global_certificate_capable=False`.

Tested behavior:

- Probe:
  `BPC_future/results/probe_replacement_repair_cb_guided_dispatchfix_tranq10_09_20260606.csv`.
- Overrides:
  `journey_replacement_repair_enabled=True`,
  `journey_replacement_repair_time_limit=6.0`,
  `journey_replacement_repair_completion_bound_enabled=True`,
  `journey_replacement_repair_completion_bound_two_cycle_enabled=True`.
- Result still stayed root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=119.07527`, `columns=493`,
  `primal=203.102839`.
- The new path did execute as intended:
  replacement repair at `cg_iter=21` had `completion_bound_enabled=True`,
  `two_cycle_table_complete=True`, `bound_build_time=2.204536`, and selected
  `4` replacement-only true-RC negative journeys.
- It was still insufficient.  A later completion-bound retry at `cg_iter=26`
  selected another `5` replacement-only journeys and the root did not certify
  before the 120s engineering limit.

Decision:

- Keep the direct-only dispatch fix; without it, direct-label-only worker
  configs silently run the wrong oracle.
- Keep CB-guided replacement repair as opt-in only.  It is exact-safe and now
  does what it says, but current evidence says it mostly moves replacement-only
  work earlier rather than removing the proof tail.
- Do not enable it in the 5/10/20 mainline configs unless paired with a stronger
  policy that converts these physical replacements into fewer tail rounds or a
  faster final certificate.

## 2026-06-06: Direct-Only Pricing Dispatch Fix Mainline Probe

Context:

- The CB-guided replacement repair probe exposed a dispatch bug: when
  `profile_pricing_enabled=False` and `direct_journey_label_pricing_enabled=True`,
  `price_journeys()` fell through to the legacy timed-trip selection path instead
  of direct-label pricing.
- This affected more than replacement repair.  Hidden-negative patrol modes also
  run as direct-only workers, so prior patrol probes may have partially measured
  the wrong oracle.

Change:

- `price_journeys()` now dispatches direct-label / NG-DSSR before the legacy
  timed-trip path whenever profile pricing is disabled and direct-label pricing
  is explicitly enabled.

Tested behavior:

- Mainline hard probe after the dispatch fix:
  `BPC_future/results/probe_direct_dispatchfix_mainline_tranq10_09_20260606.csv`.
- Result still stayed root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=119.089723`, `columns=485`,
  `primal=203.102839`.
- The behavior did change materially:
  hidden-negative patrol now logged direct-label harvesting fields and found
  replacement-only columns quickly, for example `cg_iter=13` found `4`
  replacement-only journeys in about `0.52s`.
- Completion-bound retry moved earlier and had more budget:
  at `cg_iter=14`, with about `46s` remaining, it selected `12` journeys
  (`1` new task set and `11` replacements).  A later CB retry at `cg_iter=17`
  selected `8` replacement-only journeys.

Decision:

- Keep the dispatch fix.  It corrects a real oracle-routing bug and makes worker
  names match the implementation.
- The hard root is still not solved.  The updated evidence reinforces the current
  bottleneck: direct-label patrol and CB can find replacement-heavy columns, but
  the root tail still lacks either a decisive new-task-set batch or a fast final
  no-negative certificate.
- Earlier patrol-related failed probes should be interpreted cautiously if they
  were run before this dispatch fix.

Follow-up after dispatch fix:

- Probe:
  `BPC_future/results/probe_dispatchfix_patrol_repl_escalate_tranq10_09_20260606.csv`
  with `journey_hidden_negative_patrol_replacement_only_escalates_to_cb=True`.
- Result still stayed root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=115.19975`, `columns=490`,
  `primal=203.102839`.
- The escalation did execute under the corrected direct-label patrol:
  `cg_iter=13` patrol found `2` replacement-only journeys, escalated to CB, and
  CB selected `15` replacement-only journeys.  Subsequent ordinary pricing did
  find new task-set columns, but the root still did not certify.
- A second escalation at `cg_iter=19` again produced a replacement-only CB batch
  (`5` columns) and the solve timed out.

Decision update:

- Keep `journey_hidden_negative_patrol_replacement_only_escalates_to_cb` opt-in.
  After the dispatch fix it has a slightly more plausible shape, but current
  evidence still says it moves replacement work earlier rather than producing a
  final certificate.

## 2026-06-06: Completion-Bound Arc Enumeration Cache

Context:

- Completion-bound / two-cycle final probes repeatedly enumerate the same
  coarse-state physical arc transitions while building the memoryless table and
  the two-cycle table.
- This is exact-safe to cache only inside one `_DirectJourneyCompletionBound`
  instance, because that instance is already tied to one data object, dual
  vector, branch/config choice, and build deadline.

Change:

- Added per-bound-instance caches for `_task_transitions(...)` and
  `_return_arc_completion_candidates(...)`.
- Added a toy unit test that verifies the caches are populated, repeated helper
  calls reuse the same tuple object without growing the cache, and `partial_value`
  matches a fresh bound with identical inputs.

Tested behavior:

- Targeted tests passed:
  `test_direct_journey_completion_bound_caches_arc_enumeration`,
  `test_direct_journey_completion_bound_state_is_node_time_energy_only`,
  `test_direct_journey_completion_bound_two_cycle_depot_immune_and_budget_fallback`,
  `test_direct_journey_label_two_cycle_completion_bound_audit_passes`,
  plus five related pricing/certificate tests.
- Hard probe:
  `BPC_future/results/probe_cb_arc_cache_tranq10_09_20260606.csv`.
- Result still stayed root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=119.231446`, `columns=498`,
  `primal=203.102839`.
- The cache did reduce CB build cost on the observed CB call:
  `bound_build_time=1.52857`, `two_cycle_build_time=1.507342`, compared with
  earlier mainline CB calls around `2.00s`.
- It did not change the bottleneck class.  The probe still spent the tail at
  the root with flat objective and continuing hidden negative discovery; most
  direct-label harvests were replacement-only, and the final seconds still
  found a new task-set negative column rather than a no-negative certificate.

Decision:

- Keep the cache.  It is small, exact-safe, and lowers the fixed cost of each
  CB/Final Judge table build.
- Do not treat it as a tail solver.  The next high-leverage work remains the
  six-priority queue: hidden-negative audit, Final Judge harvesting/trigger
  control, worker batching semantics, and tail dual-center stabilization.

## 2026-06-06: Hidden-Negative Profile Catalog Seeding In Mainline

Context:

- Priority 2 says that when true-dual direct-label / CB constructs hidden
  negative journeys, their feasible timed sorties can be seeded back into the
  physical profile catalog so later worker calls do not rediscover the same
  physical route from scratch.
- The seeding implementation already existed but the 5/10/20 mainline configs
  had `journey_hidden_negative_profile_catalog_seed_enabled=False`.

Change:

- Enabled `journey_hidden_negative_profile_catalog_seed_enabled=True` in the
  5-task, 10-task, and 20-task mainline configs.
- Added a config validator guard: this flag now requires
  `journey_pricing_profile_labeling_physical_catalog_resume_enabled=True`.

Tested behavior:

- 5-task full smoke:
  `BPC_future/results/probe_profile_seed_tasks5_20260606.csv` stayed exact and
  fast: Apollo15 `2.129437s`, Tranquillitatis `1.397363s`, both `OPTIMAL`.
- Hard 10-task probe:
  `BPC_future/results/probe_profile_seed_tranq10_09_20260606.csv`.
- Result still stayed root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=119.065347`, `columns=495`,
  `primal=203.102839`.
- The seed mechanism executed and inserted `21` profiles over `6` events.  It
  modestly reduced work versus the previous cache-only probe
  (`pricing_calls=61` vs `64`, `exact_pricing_calls=34` vs `35`) but did not
  repair the hard tail.

Decision:

- Keep enabled for now.  It is a bounded worker-universe repair, not a
  certificate shortcut, and the probe showed slight call-count improvement
  without harming 5-task performance.
- Do not over-credit it.  The hard case still times out because late hidden
  negatives keep appearing and the CB batch is still replacement-heavy.

## 2026-06-06: Skip-Short-Exact Tail Probe

Context:

- `journey_skip_short_exact_after_retry_negative_enabled` can reduce control
  flow churn after repeated local no-column followed by negative-column
  discoveries.  It does not alter certificate semantics.

Tested behavior:

- Probe:
  `BPC_future/results/probe_profile_seed_skipshort_tranq10_09_20260606.csv`.
- Temporary overrides:
  `journey_skip_short_exact_after_retry_negative_enabled=True`,
  `journey_skip_short_exact_min_retry_negative_rounds=2`,
  `journey_skip_short_exact_min_cg_iter=10`.
- Result still stayed root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=119.205312`, `columns=497`,
  `primal=203.102839`.
- The gate triggered `11` times, but total exact calls did not improve versus
  the profile-seed probe (`exact_pricing_calls=34` in both).  The same single
  CB retry occurred and selected replacement-only columns.

Decision:

- Do not enable skip-short-exact in the mainline configs.  It changed tail
  cadence but did not reduce the proof bottleneck.

## 2026-06-06: Learning True-RC Profile Catalog Seeding

Context:

- After enabling profile-catalog seeding, logs showed exact / CB hidden
  negatives were seeded, but true-RC-filtered learning worker columns were not.
- Learning pricing uses isolated caches by design, so any true-RC kept
  learning journeys must be explicitly seeded into the true-dual physical
  catalog if they are to repair later workers.

Change:

- When learning-smoothed pricing is active and true-RC filtering keeps columns,
  the kept journeys are now seeded into the main true-dual physical profile
  catalog before being added to the journey pool.
- The seed uses the ordinary exact/profile config and official SCIP duals, not
  the smoothed-dual isolated learning cache.

Tested behavior:

- 5-task full smoke:
  `BPC_future/results/probe_learning_seed_tasks5_20260606.csv` stayed exact and
  fast: Apollo15 `2.125637s`, Tranquillitatis `1.38648s`, both `OPTIMAL`.
- Hard 10-task probe:
  `BPC_future/results/probe_learning_true_rc_seed_tranq10_09_20260606.csv`.
- Result still stayed root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=117.963738`, `columns=495`,
  `primal=203.102839`.
- The new learning seed path executed: `heuristic_learning_true_rc` contributed
  `10` seeded profiles over `4` events.  Total seeded profiles rose from `21`
  to `30`.
- Work decreased modestly versus profile-seed only:
  `pricing_calls=59` vs `61`, `exact_pricing_calls=33` vs `34`.

Decision:

- Keep this code path.  It is exact-safe, bounded by true-RC-kept learning
  columns, and turns learning discoveries into reusable worker catalog entries.
- It is still not enough for the hard root tail; the next bottleneck remains
  Final Judge quality/triggering and late hidden-negative task-set discovery.

## 2026-06-06: Learning Dual-Center Probe

Context:

- The GNN anchor may drift from the current RMP dual face.  The learning
  runtime has an optional dual-center EMA that blends the GNN anchor with
  recent official task-cover duals only for smoothed worker pricing.

Tested behavior:

- Probe:
  `BPC_future/results/probe_profile_seed_learning_center_tranq10_09_20260606.csv`.
- Temporary overrides:
  `journey_learning_dual_center_enabled=True`,
  `journey_learning_dual_center_weight=0.5`,
  `journey_learning_dual_center_momentum=0.5`,
  `journey_learning_dual_center_min_rounds=3`.
- Result still stayed root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=119.230211`, `columns=495`,
  `primal=203.102839`.
- It reduced pricing calls substantially (`48` vs `61`) and exact calls (`25`
  vs `34`), but it also invoked two CB calls totaling about `29.3s` of CB
  search and still did not reach the certificate.
- Learning kept columns did not improve (`7` kept versus `8` in the seed-only
  probe).

Decision:

- Do not enable learning dual center by default yet.  It changes control flow
  and reduces call count, but current evidence does not prove a better hard
  tail or improved kept true-RC rate.
- If revisited, tune it together with CB trigger policy, not as a standalone
  switch.

## 2026-06-06: Current Mainline 180s Hard-10 Probe

Context:

- The 120s hard-10 failure could have been either a small final-certificate
  timing miss or a deeper root-tail loop.  To distinguish the two, the current
  mainline was run on
  `tranquillitatis_balmer_like_20km_tasks10_09_seed11144` with a `180s`
  wall-clock limit.

Tested behavior:

- Probe:
  `BPC_future/results/probe_current_tranq10_09_180s_20260606.csv`.
- Result still stayed root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=179.165742`, `nodes=1`, `columns=498`,
  `primal=203.102839`.
- Completion-bound retries still returned replacement-only batches:
  the first CB retry at `cg_iter=21` had `96` true-RC negative candidates,
  `12` selected, and `0` candidate/selected new task sets.  Later CB retries
  at `cg_iter=29` and `31` again selected only replacement task sets.
- The CB-found task sets were mostly not repeats; they were different existing
  task sets whose physical representatives were still not the cheapest known
  direct-label realizations.  Therefore the failure is not just a 120s reserve
  issue.  The Final Judge is still being used as a physical-representative
  repair worker.

Decision:

- Do not interpret hard-10 as “almost certified after 120s.”  Even 180s does
  not close the root.
- The next code direction should reduce replacement-only CB work before the
  final proof.  A low-risk foundation has been added: `_add_priced_journeys`
  now returns `new_task_sets`, `replacement_task_sets`, and
  `changed_task_sets`, so a future repair worker can target only the task sets
  changed in the current round instead of scanning the whole replacement
  universe.

## 2026-06-06: Targeted Replacement Repair By Recent Changed Task Sets

Context:

- The broad replacement-repair worker previously timed out because it scanned
  the whole known task-set replacement universe.
- A narrower implementation was added:
  `_add_priced_journeys` records `changed_task_sets`,
  `_journey_replacement_repair_config` accepts `target_task_sets`, and
  direct-label repair intersects the dominant-task-set masks with this explicit
  target list.
- The default remains fail-closed: with
  `journey_replacement_repair_target_recent_changed_task_sets_only=True`, the
  repair worker does not run unless there is at least one recent changed task
  set.

Tested behavior:

- Probe:
  `BPC_future/results/probe_targeted_repair_tranq10_09_20260606.csv`.
- Override:
  `journey_replacement_repair_enabled=true`.
- Result stayed root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=119.087367`, `primal=203.102839`,
  `columns=495`.
- The targeted worker did run at `cg_iter=21` with `target_task_sets=1`, so the
  scope restriction was active.
- It still returned no columns:
  `pricing_state=INCOMPLETE_LIMIT`, `reason=time_limit`,
  `negative_journeys=0`, `generated_sequences=102112`,
  `evaluated_timed_trips=15630`.
- The following completion-bound retry was still needed and returned only
  replacement columns:
  `direct_label_harvest_candidate_count=96`,
  `direct_label_harvest_selected_count=12`,
  `direct_label_harvest_selected_new_task_set_count=0`,
  `direct_label_harvest_selected_replacement_task_set_count=12`.

Decision:

- Keep the targeted-repair infrastructure because it is exact-safe and prevents
  accidental global repair scans when the switch is enabled.
- Do not enable `journey_replacement_repair_enabled` by default.  Even a single
  targeted task set can trigger a costly direct-label search without finding
  the hidden replacement columns before CB.
- The next useful direction is not more replacement-only repair.  Focus on
  priority 3/5: make the ordinary/profile worker return larger true-RC batches
  and make Final Judge harvesting convert an expensive CB visit into broader
  RMP progress.

## 2026-06-06: Cross-Count Frontier Lookup Regression

Context:

- Profile DP cross-count dominance scans a large number of same-mask labels in
  hard tail rounds.
- A per-mask `_CrossCountLabelFrontier` was tested to replace the old bucket
  scan with a sorted nondominated `(end_time, value)` frontier.
- The change was exactness-preserving in targeted unit tests and did not hurt
  5-task smoke instances.

Tested behavior:

- Baseline kept micro-optimizations only:
  `probe_mask_filter_cache_tranq10_09_20260606.csv`.
- Frontier probes:
  `probe_cross_frontier_tranq10_09_20260606.csv` and
  `probe_cross_frontier_bisect_tranq10_09_20260606.csv`.
- On hard `tranquillitatis_balmer_like_20km_tasks10_09_seed11144`, the frontier
  did not close the root within 120s and increased exact profile-DP work:
  `profile_dp_time` rose from about `22.15s` to about `25.9s`,
  `dp_profile_record_scans` rose from about `3.37M` to about `4.00M`, and
  `dp_state_count` rose from about `292.9k` to about `336.6k`.

Decision:

- Do not keep or enable the cross-count frontier as a default optimization.
- The old cross-count bucket scan is currently the safer hard-tail path.
- Future attempts need to prove lower profile-DP time on hard-10 cases, not
  only pass local dominance tests or 5-task smoke runs.

## 2026-06-06: Allowing Duplicate Task Sets In CB Harvest Is Mostly Noise

Context:

- The hard `tranquillitatis_balmer_like_20km_tasks10_09_seed11144` tail showed
  completion-bound Final Judge had many true-RC negative physical candidates
  but selected only `12` replacement task sets when duplicate task sets were
  blocked.
- A probe enabled
  `journey_certificate_completion_bound_diverse_harvest_allow_duplicate_task_sets=true`
  to test whether the expensive judge should fill the batch with more physical
  representatives from the same task set.

Tested behavior:

- Probe:
  `BPC_future/results/probe_cb_harvest_dup_tasks_tranq10_09_20260606.csv`.
- Result stayed root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=115.667709`, `columns=482`,
  `primal=203.102839`.
- Completion-bound selected `20 + 20` journeys across two retries, but most of
  them did not change the RMP pool:
  first CB addition `requested=20`, `added=4`, `unchanged=16`;
  second CB addition `requested=20`, `added=1`, `unchanged=19`.
- The reason is structural: multiple physical representatives for the same
  task set compete inside one batch.  Once the cheapest one updates the pool,
  the remaining same-task-set representatives become unchanged.

Decision:

- Do not enable duplicate task sets in completion-bound harvesting by default.
- The current default, one selected representative per task set, wastes fewer
  RMP add attempts and better matches the “orthogonal harvest” intent.
- If this is revisited, the selector should still keep at most one physical
  representative per task set per batch unless it can prove each additional
  representative will improve the current pool after earlier selected
  replacements.

## 2026-06-06: Post-Seed Profile Reharvest Does Not Consume CB Seeds Usefully Yet

Context:

- A short true-dual profile worker was added after hidden-negative/CB seeding:
  `_journey_post_seed_profile_reharvest_config`.
- Its intended role was priority-5 worker batching: once direct-label or
  completion-bound pricing seeds physical profiles into the catalog, run a
  non-certificate profile pass immediately before the next RMP solve.
- The worker was explicitly marked `certificate_capable=False`; it never
  replaces the true-dual final judge.

Tested behavior:

- Probe:
  `BPC_future/results/probe_post_seed_reharvest3_tranq10_09_20260606.csv`.
- Hard instance:
  `tranquillitatis_balmer_like_20km_tasks10_09_seed11144`.
- Result stayed root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=118.347755`, `primal=203.102839`,
  `columns=498`.
- The reharvest worker did trigger once after CB selected `12`
  replacement-only journeys:
  `event=journey_post_seed_profile_reharvest`, `remaining=15.203710`,
  `time_limit=1.5`.
- It spent about `1.16s` (`profile_generation_time=0.049788`,
  `profile_dp_time=1.115002`), scanned `175397` profile records, and returned
  no usable journeys:
  `reason=negative_journeys_already_in_pool`, `negative_journeys=0`.
- The next rounds still needed ordinary exact / hidden patrol calls and the
  run timed out.  The worker did not reduce the certificate tail.

Decision:

- Keep the code path and unit-level config helper as an opt-in diagnostic
  switch.
- Do not enable `journey_post_seed_profile_reharvest_enabled` in the 5/10/20
  mainline configs.  In its current form it mostly re-discovers the already
  seeded CB profiles and adds profile-DP overhead.
- Future work should not retry this exact worker shape.  If revisited, it must
  prove that it materializes new task sets or strictly better replacement
  columns after seed, not merely `negative_journeys_already_in_pool`.

## 2026-06-06: Late Cross-Count Materialization Adds Work Without Tail Progress

Context:

- Hidden-negative audit on hard `tranq10_09` showed several patrol-found
  negative journeys where the ordinary worker had already hit the hidden task
  mask and sortie mask, but the primary miss reason was
  `profile_cross_count_dominance`.
- The code already supports materializing labels pruned by cross-count
  dominance via
  `journey_pricing_late_profile_cross_count_true_rc_materialization_*`.
- A small late-only budget was tested instead of disabling cross-count
  dominance globally.

Tested behavior:

- Probe:
  `BPC_future/results/probe_cross_count_materialization_tranq10_09_20260606.csv`.
- Temporary config:
  `journey_pricing_late_profile_cross_count_true_rc_materialization_slack=2.0`,
  `journey_pricing_late_profile_cross_count_true_rc_materialization_max_candidates=48`.
- Result stayed root `TIME_LIMIT` and worsened slightly:
  `status=TIME_LIMIT`, `solving_time=120.072861`, `primal=203.102839`,
  `columns=498`.
- The mechanism did fire:
  exact pricing accumulated `profile_cross_count_materialization_candidate_count=71`
  and `profile_cross_count_materialization_selected_candidate_count=37`.
- Those candidates did not become useful columns.  The hard tail still needed
  hidden patrol and CB; additional exact-retry calls appeared, and
  `weak_negative_journeys_filtered` increased.

Decision:

- Do not enable late cross-count materialization in mainline configs.
- The hidden negatives in this run are not solved by simply materializing
  cross-count-pruned labels; the selected materialization candidates are mostly
  weak or already dominated under true RC.
- Future work should look at the exact true-RC filter / replacement-only
  behavior or broader tail dual-center effects rather than increasing this
  materialization budget.

## 2026-06-06: Requiring New Task Sets For CB Soft Return Did Not Break The Tail

Context:

- Priority 3 suggested preventing the completion-bound Final Judge from returning
  replacement-only soft-return batches, because replacement batches do not widen
  the RMP task-set directions.
- The existing direct-label soft-return helper already supports
  `journey_certificate_completion_bound_diverse_harvest_soft_return_min_new_task_sets`.
  A probe temporarily set this to `1` in the 5/10/20 mainline configs.

Observed behavior:

- Probe:
  `BPC_future/results/probe_softreturn_minnew1_tranq10_09_20260606.csv`.
- Hard instance:
  `tranquillitatis_balmer_like_20km_tasks10_09_seed11144`.
- Result stayed root `TIME_LIMIT`:
  `status=TIME_LIMIT`, `solving_time=118.24151`, `nodes=1`, `columns=476`,
  `rmp_solves=21`, `pricing_calls=48`, `exact_pricing_calls=27`.
- The new-task-set soft-return gate did not hit the critical path.  The final
  completion-bound retry happened only at the end, returned `18` replacement
  task sets and `0` new task sets with `direct_label_harvest_soft_return_triggered=False`,
  then hit the time limit.
- Earlier tail rounds were still dominated by ordinary/profile no-column,
  hidden-negative patrol, and replacement-only additions.

Decision:

- Reverted the mainline config change and the corresponding config invariant
  assertion.
- Do not enable a positive soft-return new-task-set minimum by default.  It does
  not solve the current hard-tail bottleneck because the problematic replacement
  batch is returned under time-limit/incomplete behavior rather than the soft
  return path.
- Future work should target why new task-set directions disappear before the
  Final Judge, or why strong exact certificates previously closed with more cuts,
  rather than gating an already late replacement-only timeout batch.

## 2026-06-06: Static SRC Budget 160 Does Not Restore The Old 58s Hard-10 Path

Context:

- An older pre-status-semantics probe,
  `BPC_future/results/probe_tranq10_09_after_ng_memory_switch_20260604.csv`,
  solved hard `tranq10_09` in `58.340447s` with `subset_row_cuts_added=160`.
- The current 10-task mainline uses `static_subset_row_cut_budget=120` and
  exact certificate semantics.  A probe tested whether restoring the visible
  static-SRC count to `160` would recover the faster path.

Observed behavior:

- Probe:
  `BPC_future/results/probe_static_src160_current_tranq10_09_20260606.csv`.
- Run used `active_cuts=161` and `subset_row_cuts=160`, matching the old static
  cut count, but still timed out at the root:
  `status=TIME_LIMIT`, `solving_time=119.233243`, `nodes=1`, `columns=486`,
  `rmp_solves=25`, `pricing_calls=54`, `exact_pricing_calls=29`.
- The tail still required hidden-negative patrol and completion-bound retry:
  `cg_iter=14` CB found `8` selected journeys (`1` new task set, `7`
  replacements) and `cg_iter=23` CB found only replacement task sets before the
  final timeout.
- The old 58s log lacks the explicit `pricing_state` and
  `global_certificate_capable` fields added later, so it should not be treated as
  proof that the current exact-safe certificate chain can be recovered by a cut
  budget rollback alone.

Decision:

- Do not change the default static SRC budget from `120` to `160` based on the
  old run.  It increases tail calls in the current code path and does not restore
  a root certificate within the 120s engineering limit.
- Avoid further blind static-SRC budget sweeps.  Future SRC work should change
  activation timing or selection quality with current certificate semantics, not
  simply chase the old static cut count.

## 2026-06-06: Root Heuristic Flat-Weak Continuation Is Semantically Right But Not Sufficient

Context:

- The B&B node loop already treated small objective-flat batches as weak
  pressure: weak heuristic batches may fall through to exact pricing in the
  same CG iteration, and weak exact batches do not reset the no-column pressure.
- The legacy root-only loop did not mirror the heuristic half of this behavior.
  It could treat a small learning/profile worker batch as full progress and
  immediately continue to the next RMP solve.

Change:

- Mirrored the node-loop behavior in the root loop for heuristic/learning
  worker additions:
  `journey_certificate_flat_weak_column_pressure_enabled` now also logs
  `journey_flat_weak_column_pressure` at root, tracks
  `certificate_flat_weak_column_rounds`, and lets weak heuristic additions
  continue to true-dual exact pricing when
  `journey_certificate_flat_weak_column_continue_exact_after_heuristic` says so.

Probe:

- `BPC_future/results/probe_root_flatweak_tranq10_09_20260606.csv`
  on hard 10-task `tranq10_09`, 120s limit.
- Result stayed root `TIME_LIMIT`:
  `solving_time=118.395663`, `columns=495`, `rmp_solves=26`,
  `pricing_calls=60`, `exact_pricing_calls=34`.
- The new root heuristic path did trigger:
  at `cg_iter=22` and `23`, heuristic additions logged
  `weak=True` and `continue_exact=True`, followed by exact pricing in the same
  iteration.
- The final bottleneck remained certificate tailing.  At `cg_iter=26`, the
  completion-bound final probe started with only about `7.8s` remaining, was
  handed a `6.0s` budget, and timed out without a certificate:
  `pricing_state=INCOMPLETE_LIMIT`, `reason=time_limit`.

Decision:

- Keep the root heuristic weak-pressure fix because it aligns root and node
  semantics and is exact-safe.
- Do not expect this alone to solve the hard tail.  The remaining issue is that
  true-dual workers keep exposing small batches before the final judge has
  enough time to certify.

## 2026-06-06: Larger Final-Reserve Probe Still Times Out

Context:

- After the root weak-pressure fix, the hard `tranq10_09` run still reached the
  final completion-bound judge too late.  A narrow probe tested whether a more
  aggressive final reserve would give the judge enough time.

Probe:

- `BPC_future/results/probe_finalreserve12_tranq10_09_20260606.csv`.
- Temporary overrides:
  `journey_certificate_completion_bound_pre_retry_reserve_time=12.0` and
  `journey_certificate_completion_bound_after_retry_min_time=10.0`.
- Result stayed root `TIME_LIMIT`:
  `solving_time=116.987854`, `columns=498`, `rmp_solves=29`,
  `pricing_calls=66`, `exact_pricing_calls=37`.

Observed behavior:

- The larger minimum final-probe time did not yield a certificate.  It mostly
  let ordinary exact/profile workers keep running and returning small batches:
  late exact calls at `cg_iter=27` and `28` still found only `3` and `1`
  true-dual negative journeys.
- The final completion-bound retry barely appeared; increasing the minimum
  final-probe time can prevent the final judge from launching when remaining
  time is below the new threshold.

Decision:

- Do not raise `journey_certificate_completion_bound_after_retry_min_time` or
  pre-reserve globally based on this probe.
- The bottleneck is not simply "the final judge needs a bigger last slice";
  it is the degeneracy loop where ordinary true-dual pricing keeps exposing
  only a few new task-set directions per RMP extreme point.  Future work should
  focus on stronger tail dual-center workers or a broader exact-safe harvesting
  mechanism that reduces those small-batch RMP pivots without turning CB into a
  replacement-only worker.

## 2026-06-06: L1 Stabilized Dual With DOI/DDOI Does Not Break The Hard-10 Tail

Context:

- A probe tested whether tail-only stabilized duals plus dual-optimal
  inequalities could reduce the root dual ping-pong on hard `tranq10_09`.
- Temporary overrides enabled:
  `journey_dual_stabilization_enabled=true`,
  `journey_dual_stabilization_tail_only_enabled=true`,
  `journey_dual_stabilization_certificate_candidate_enabled=true`,
  `journey_dual_stabilization_mode=l1_reference`,
  `journey_dual_stabilization_time_limit=0.5`,
  `journey_dual_optimal_inequalities_enabled=true`, and
  `journey_deep_dual_optimal_inequalities_enabled=true`.

Probe:

- `BPC_future/results/probe_dual_stab_l1_doi_tranq10_09_20260606.csv`.
- Result stayed root `TIME_LIMIT`:
  `solving_time=119.063924`, `columns=483`, `nodes=1`.
- Stabilized duals were accepted in several tail rounds and DOI/DDOI were
  constructed (`doi_cover_bounds=10`, `ddoi_pair_bounds=45`), but the tail still
  reached local no-column / completion-bound retry states without a certificate.
- Late completion-bound calls again produced replacement-heavy batches rather
  than enough new primal-support directions.

Decision:

- Do not promote this DOI/DDOI + L1 reference configuration as a default fix.
- The useful conclusion is diagnostic: the current bottleneck is less "missing
  any dual stabilization object" and more "the columns returned under tail duals
  rarely alter active RMP support enough to move the primal face."  Future work
  should measure active-support impact on every `journey_column_addition` event
  before another broad dual-stabilization sweep.

## 2026-06-06: Pre-Exact Completion-Bound Handoff Does Not Break The Hard-10 Tail

Context:

- The six-priority roadmap says CB / Final Judge must be controlled carefully:
  it should appear in the certificate tail, not become an early negative-column
  worker.
- A root-only pre-exact handoff was added as exact-safe infrastructure:
  after enough flat certificate-candidate rounds, ordinary exact pricing may
  hand the tail directly to completion-bound final judge if remaining time is
  within the configured protection window.
- Active-support impact logging was also added to `journey_column_addition`.
  It separates columns that change a task set present in the current positive
  LP support from columns that only add inactive directions.

Observed behavior:

- Probe:
  `BPC_future/results/probe_pre_exact_handoff_tranq10_09_20260606.csv`.
  Result stayed root `TIME_LIMIT`: `solving_time=119.221715`,
  `columns=495`.
- Probe with active-support weak-column pressure and a larger protection
  window:
  `BPC_future/results/probe_activeweak_handoff_tranq10_09_20260606.csv`.
  Result stayed root `TIME_LIMIT`: `solving_time=119.234732`,
  `columns=485`.
- The handoff triggered earlier, but it still returned replacement-heavy
  batches and did not hit active support.  Completion-bound calls at late
  iterations selected small batches whose
  `active_changed_task_set_count` remained `0`.

Decision:

- Keep the handoff code path and active-support diagnostics as opt-in /
  guarded infrastructure.
- Do not treat "handoff to CB earlier" as a default performance fix by itself.
  In this hard case it risks making CB an expensive worker unless final-judge
  harvesting produces genuinely new or active-support-relevant directions.
- The key diagnostic is now active support impact, not just number of negative
  columns returned.

## 2026-06-06: Disabling Completion-Bound Elapsed Soft Return Is Not Enough

Context:

- Completion-bound diverse harvesting had a soft-return path that could return
  after a short elapsed time with a small number of replacement columns.
- Hypothesis: once the expensive final judge has started, it should spend the
  local budget and harvest more columns rather than return after a few weak
  replacements.

Observed behavior:

- Probe:
  `BPC_future/results/probe_cb_no_soft_return_tranq10_09_20260606.csv`.
- Result stayed root `TIME_LIMIT`: `solving_time=119.207439`,
  `columns=496`.
- The first completion-bound retry did harvest more columns:
  at `cg_iter=17`, it selected `20` of `256` candidates with soft return
  disabled.
- However, almost all selected columns were still replacement directions:
  `candidate_new_task_set_count=1`, `selected_new_task_set_count=1`, and
  `selected_replacement_task_set_count=19`.  Active-support impact remained
  absent.

Decision:

- Keep the elapsed-soft-return switch as a useful diagnostic / scheduling
  guard.
- Do not rely on "spend more CB time" alone.  If the candidate universe itself
  is replacement-heavy, disabling soft return only increases batch size without
  changing the RMP face enough to close the root.

## 2026-06-06: New-Task-Set Quota In Final-Judge Harvesting Did Not Help When No New Candidates Exist

Context:

- A new exact-safe selector option,
  `direct_journey_label_diverse_harvest_min_new_task_sets`, was added so the
  final judge can reserve part of its harvest budget for new task-set
  directions before filling with strongest replacements.
- The intent is to avoid a strong true-RC replacement column crowding out a
  slightly weaker but more useful new task-set direction.

Observed behavior:

- Probe:
  `BPC_future/results/probe_harvest_newquota_tranq10_09_20260606.csv`.
- Result stayed root `TIME_LIMIT`: `solving_time=118.242534`,
  `nodes=1`, `columns=476`, `rmp_solves=21`, `pricing_calls=46`,
  `exact_pricing_calls=25`.
- The single late completion-bound pre-exact handoff selected `18` journeys,
  but all were replacements:
  `direct_label_harvest_candidate_new_task_set_count=0`,
  `direct_label_harvest_selected_new_task_set_count=0`,
  `direct_label_harvest_selected_replacement_task_set_count=18`.
- Late `journey_column_addition` events from `cg_iter=10` onward consistently
  showed `active_changed_task_set_count=0`; the returned negative columns did
  not touch current active LP support.

Decision:

- Keep the new-task-set quota as exact-safe harvesting infrastructure and keep
  its unit test: it is useful when new candidates exist.
- Do not expect the quota to solve hard `tranq10_09` by itself.  In the observed
  tail, the final judge had no new task-set candidates to reserve.
- The next useful optimization should address why the tail dual/primal face
  only exposes inactive replacement columns, likely through a stronger tail dual
  center or a worker that targets active-support-changing directions before CB
  is invoked.

## 2026-06-06: Averaged-Dual Direct Patrol Finds Columns But Still Misses Active Support

Context:

- A previous dual-averaging probe failed because the averaged dual was passed
  through the normal profile worker: it produced negative average-RC structure
  but true-RC filtering rejected or dominated almost everything.
- A narrower worker-only path was added:
  `journey_dual_averaging_direct_patrol_enabled`.  When historical dual
  averaging activates, this option routes the averaged-dual worker through the
  bounded direct-label hidden-negative patrol instead of the profile worker.
  Every returned journey is still filtered by the latest true dual; no-column is
  never a certificate.

Observed behavior:

- Probe:
  `BPC_future/results/probe_dual_avg_direct_patrol_tranq10_09_20260606.csv`.
- Overrides:
  `journey_dual_averaging_enabled=true` and
  `journey_dual_averaging_direct_patrol_enabled=true`.
- Result stayed root `TIME_LIMIT`: `solving_time=118.480336`,
  `columns=475`.
- The new worker did run and found one addable true-RC negative journey at
  `cg_iter=13`, but it was still inactive with respect to the current LP
  support (`active_changed_task_set_count=0`).  One following failed averaged
  patrol triggered the existing strict cooldown and disabled further attempts
  until late in the run.

Cooldown follow-up:

- Probe:
  `BPC_future/results/probe_dual_avg_direct_patrol_cool3_tranq10_09_20260606.csv`.
- Additional overrides:
  `journey_dual_averaging_true_rc_filter_fail_patience=3` and
  `journey_dual_averaging_true_rc_filter_fail_cooldown_rounds=3`.
- Result stayed root `TIME_LIMIT`: `solving_time=118.228222`,
  `columns=482`, `rmp_solves=24`, `pricing_calls=52`.
- The worker fired more often and kept true-RC negative columns at
  `cg_iter=13`, `15`, and `22`, but every late addition still had
  `active_changed_task_set_count=0`.  Several averaged-dual candidates were
  strongly negative under the averaged dual but positive under the latest true
  dual.

Decision:

- Keep `journey_dual_averaging_direct_patrol_enabled` as opt-in infrastructure.
  It is exact-safe and a better diagnostic than the old profile-based averaged
  worker.
- Do not enable it by default in the 5/10/20 configs.  It increases worker
  activity and can find some true-RC columns, but on hard `tranq10_09` those
  columns still do not touch the active LP support and do not shorten the tail.
- Future tail-dual work should become active-support-aware rather than merely
  changing the dual center used by another worker.

## 2026-06-06: Active-Support-Aware Harvesting Has No Active Candidates In Hard `tranq10_09`

Context:

- Late hard-10 logs repeatedly showed `active_changed_task_set_count=0`.
  A natural follow-up was to make diverse direct-label harvesting prefer
  candidates whose task set is currently in the positive LP support.
- Added an opt-in selector quota:
  `direct_journey_label_diverse_harvest_min_priority_task_sets`, with driver
  passing current active-support task sets as `priority_task_sets` for exact
  direct-label pricing.  This only changes the ordering among already
  true-RC-negative candidates; it cannot certify a node and does not change
  reduced-cost formulas.

Observed behavior:

- Probe:
  `BPC_future/results/probe_active_priority_harvest_tranq10_09_20260606.csv`.
- Override:
  `journey_certificate_completion_bound_diverse_harvest_min_priority_task_sets=5`.
- Result stayed root `TIME_LIMIT`: `solving_time=118.460405`,
  `columns=476`, `nodes=1`.
- The completion-bound pre-exact handoff at `cg_iter=21` reported
  `direct_label_harvest_candidate_priority_task_set_count=0` and
  `direct_label_harvest_selected_priority_task_set_count=0`.  It selected
  `18` replacement columns, but none touched the active LP support.
- Late `journey_column_addition` events from `cg_iter=10` onward still had
  `active_changed_task_set_count=0`.

Decision:

- Keep the priority-task-set harvesting hook as exact-safe infrastructure and
  retain its unit test.  It may be useful if a future bound/worker actually
  exposes active-support candidates.
- Do not enable active-priority harvest quotas by default.  In the observed
  hard tail, the active-support candidates are absent before selection, so a
  selector quota cannot fix the tail.
- The next useful direction is upstream: understand why current active LP
  support has no true-RC-improving representatives under the tail dual, or
  trigger a master-side stabilization / pool restart / cut strategy that
  changes the active face instead of adding more inactive columns.

## 2026-06-06: Do Not Discard Harvested Direct-Label Candidates At Timeout Exit

Context:

- A hard `tranq10_09` audit showed completion-bound direct-label pricing could
  collect many true-RC negative candidates and select a diverse batch, but still
  return `negative_journeys=0` when the soft min-new-task-set target was not
  met before the pricing time limit.
- This violated the intended priority-3 semantics.  The min-new-task-set target
  is a soft early-return condition for improving harvest composition; it must
  not discard already selected true-RC negative columns at the final timeout or
  incomplete exit.

Fix:

- Keep the min-new-task-set target in the direct-label early-return readiness
  check.
- Remove the final exit block that converted a non-empty selected candidate
  batch into no-column / incomplete only because the soft min-new-task-set
  target was unmet.
- The resulting columns are still ordinary feasible journeys filtered by true
  reduced cost.  Returning them is exact-safe; they do not certify no negative
  columns unless the true-dual direct-label search is exhausted.

Observed behavior after the fix:

- Probe:
  `BPC_future/results/probe_return_selected_on_cb_timeout_tranq10_09_20260606.csv`.
- Result still hit root `TIME_LIMIT`: `solving_time=119.073154`, `nodes=1`,
  `columns=476`.
- The late completion-bound pre-exact handoff at `cg_iter=21` now returned and
  added the selected batch:
  `negative_journeys=18`,
  `direct_label_harvest_candidate_count=230`,
  `direct_label_harvest_selected_count=18`,
  `direct_label_harvest_selected_new_task_set_count=0`,
  `direct_label_harvest_selected_replacement_task_set_count=18`,
  `best_reduced_cost=-1.611269`.
- The corresponding `journey_column_addition` added `18` journeys, but
  `active_changed_task_set_count=0`; the batch was still replacement-only and
  did not close the hard root.

Decision:

- Keep the fix.  It corrects the direct-label harvesting exit semantics and
  prevents useful true-RC negative columns from being thrown away.
- Do not treat it as the final performance solution.  The remaining hard-case
  bottleneck is that the selected CB/direct-label batch is still inactive with
  respect to the current LP support, so it does not move the degenerate RMP face
  enough before the outer time limit.
- Rerun earlier pre-exact handoff timing probes after this fix, because prior
  results that showed selected candidates but `negative_journeys=0` were
  partially invalidated by this exit bug.

## 2026-06-06: Existing Physical-Catalog Pre-Scan Was Not A Default Win

Context:

- A worker-level shortcut was tried for priority 5: when the dual-independent
  physical sortie catalog already exists, scan the existing catalog before
  extending it again.  The intended benefit was to avoid spending several
  seconds growing the catalog when the current true dual could already find a
  negative batch in the stored profiles.
- This is exact-safe only as a negative-column worker shortcut.  A no-column
  pre-scan result is ignored and never treated as a certificate.

Observed behavior:

- Full 5-task run:
  `BPC_future/results/all_tasks05_after_profile_prescan_20260606.csv`.
  All 20 instances solved `OPTIMAL`; average `1.105s`, max `2.153s`.
- Full 10-task run:
  `BPC_future/results/all_tasks10_after_profile_prescan_20260606.csv`.
  Only 6/20 instances solved `OPTIMAL`; average wall time `73.681s`, max
  `120.011s`.
- Compared with `BPC_future/results/all_tasks10_current_20260605.csv`, the
  old run solved 13/20.  Several Apollo15 instances that previously solved
  became `TIME_LIMIT` / incomplete, for example:
  `apollo15_20km_tasks10_03_seed11036` went from `OPTIMAL 12.131s` to
  `TIME_LIMIT 11.121s`, and `apollo15_20km_tasks10_08_seed11127` went from
  `OPTIMAL 103.078s` to `TIME_LIMIT 51.756s`.
- Re-running `apollo15_20km_tasks10_03_seed11036` after making the pre-scan
  opt-in and disabled by default still produced the same early incomplete
  status, so the broader regression is not caused solely by the pre-scan patch.
  The pre-scan is nevertheless not justified as a default because it did not
  improve the hard root cases and added another path-changing worker shortcut.

Decision:

- Keep the code only behind the disabled opt-in flag
  `profile_labeling_existing_catalog_pre_scan_enabled` /
  `journey_pricing_profile_labeling_existing_catalog_pre_scan_enabled`.
- Do not enable it in the 5/10/20 main configs.
- The next priority-1/2 issue is not catalog pre-scan.  It is the duplicate-only
  final-judge certificate chain in branch nodes.

## 2026-06-06: Branch Nodes Can Fail On Final-Judge DUPLICATE_ONLY

Context:

- During the full 10-task run after the current priority-1/3 changes, several
  Apollo15 cases returned `TIME_LIMIT` well before the 120s outer limit.  The
  representative probe
  `BPC_future/results/probe_prescan_disabled_apollo10_03_20260606.csv`
  failed at `10.947s` with gap `0.033747`.

Observed behavior:

- In `apollo15_20km_tasks10_03_seed11036`, the root node was certified by
  completion-bound direct-label pricing.
- At branch node `node_id=1`, the true-dual completion-bound final judge
  exhausted and reported:
  `status=OPTIMAL`,
  `pricing_state=DUPLICATE_ONLY`,
  `reason=negative_journeys_already_in_pool`,
  `global_certificate_capable=True`,
  `completion_bound_enabled=True`,
  `existing_journeys_filtered=998`,
  `best_reduced_cost=-63.999106`.
- The driver rejected this result with
  `direct_label_final_judge_not_no_column_certificate` and marked the node
  incomplete.  A sibling node was later certified, but the earlier incomplete
  node kept the whole B&B run from reporting `OPTIMAL`.

Interpretation:

- This is a pricing-state semantics issue, not a GNN or CB-trigger timing
  issue.  The final judge did not find a new addable column; it found only
  negative candidates already filtered as existing pool signatures.
- The next exact-safe fix should distinguish two cases:
  if duplicate-only candidates are already present in the current branch-node
  RMP column set, the node may be certifiable as "no new negative column";
  if they are only in a global pool but absent from the current node RMP, they
  must be reintroduced into the node RMP rather than filtered out.
- Do not blindly treat all `DUPLICATE_ONLY` as a global certificate.  First
  audit whether the duplicate signatures are in the current node RMP and
  whether dominated-task-set filtering is involved.

Follow-up fix:

- Added a narrow duplicate-only final-judge audit in `journey_driver.py`.
- It triggers only when the true-dual direct-label / completion-bound final
  judge is exhausted, certificate-capable, returns no addable journeys, and the
  pricing state is `DUPLICATE_ONLY` with reason
  `negative_journeys_already_in_pool`.
- The audit re-solves the current branch-node RMP with reduced costs captured.
  Because journey variables have upper bound `x_j <= 1`, existing columns may
  have negative reduced cost only if they are already at the upper bound.  The
  duplicate-only result is promoted to `CERTIFIED_NO_NEGATIVE` only when every
  negative RMP reduced-cost variable is at that upper bound; if any negative
  reduced-cost RMP variable is below the upper bound, the result remains
  uncertified.
- Representative validation:
  `probe_duplicate_audit_apollo10_03_20260606.csv` changed
  `apollo15_20km_tasks10_03_seed11036` from early `TIME_LIMIT` around 11s back
  to `OPTIMAL` in `10.907398s`.
- The audit log for that probe accepted the duplicate-only final judge at
  branch node 1 with `existing_journeys_filtered=998`, `node_journeys=84`,
  `negative_reduced_cost_count=0`, and `min_reduced_cost=0.0`.

Decision:

- Keep the audit enabled by default because it is bounded to rare final-judge
  duplicate-only exits and does not relax worker-local no-column semantics.
- Do not generalize this to profile workers or incomplete duplicate scans.
  `DUPLICATE_ONLY` remains uncertified unless this exact audit succeeds.

## 2026-06-06: Earlier CB Handoff And Active-Overlap Harvest Do Not Fix `tranq10_09`

Context:

- After the duplicate-only audit, the 10-task batch recovered to `14/20`
  `OPTIMAL`, but hard Tranquillitatis root nodes still missed the 120s
  engineering limit.
- The representative hard root remains
  `tranquillitatis_balmer_like_20km_tasks10_09_seed11144`.

Probe 1: earlier completion-bound handoff

- Command override:
  `journey_certificate_completion_bound_pre_exact_handoff_max_remaining=70.0`
  and `journey_certificate_completion_bound_pre_exact_handoff_min_flat_rounds=2`.
- Result file:
  `BPC_future/results/probe_cb_handoff70_tranq10_09_20260606.csv`.
- Outcome: `TIME_LIMIT`, primal `203.102839`, no certificate dual, time
  `119.228269s`, root-only `nodes=1`, columns `482`.
- The pre-exact handoff fired at `cg_iter=11` with about `60.13s` remaining.
  The completion-bound direct-label probe spent about `58.15s`, returned
  `13` true-RC negative columns, but all were replacements:
  `direct_label_harvest_selected_new_task_set_count=0`,
  `direct_label_harvest_selected_replacement_task_set_count=13`, and
  `active_changed_task_set_count=0`.

Interpretation:

- The problem is not simply that CB starts too late.  Starting CB earlier can
  turn it into an even more expensive worker, consuming the remaining
  certificate budget while still returning replacement-only inactive columns.
- Do not set a large default
  `journey_certificate_completion_bound_pre_exact_handoff_max_remaining` based
  on this hard case.

Probe 2: active-overlap harvest priority

- Implemented an opt-in selector knob:
  `direct_journey_label_diverse_harvest_priority_overlap_threshold` /
  `journey_certificate_completion_bound_diverse_harvest_priority_overlap_threshold`.
  It treats a true-RC negative candidate as priority when its task-set Jaccard
  overlap with a current active RMP task-set exceeds the threshold.  This only
  changes batching; it does not alter feasibility, reduced-cost filtering, or
  certificate semantics.
- Probe override:
  `journey_certificate_completion_bound_diverse_harvest_min_priority_task_sets=5`
  and
  `journey_certificate_completion_bound_diverse_harvest_priority_overlap_threshold=0.5`.
- Result file:
  `BPC_future/results/probe_priority_overlap_harvest_tranq10_09_20260606.csv`.
- Outcome: `TIME_LIMIT`, primal `203.102839`, no certificate dual, time
  `119.152174s`, root-only `nodes=1`, columns `492`.
- The late CB retry still reported
  `direct_label_harvest_candidate_priority_task_set_count=0` and selected
  `20` columns with only `2` new task sets and `18` replacements.  The added
  batch again had `active_changed_task_set_count=0`.

Decision:

- Keep the active-overlap priority code as opt-in infrastructure because it is
  exact-safe and tested, but do not enable it in the 5/10/20 main configs.
- The next useful work is not more harvest priority tuning.  For this hard
  root, hidden negative columns are physically far from the current active RMP
  support; the bottleneck is stronger certificate pruning or a different
  true-dual worker universe, not active-support-biased harvesting.

Probe 3: standalone unique-task / unique-route helper without full CB table

- Implemented an opt-in path where the unique-task and unique-route completion
  helpers can be constructed even when the full completion-bound route table is
  disabled.  This lets ordinary direct-label pricing use the helper bounds
  without paying the full CB table construction cost.
- Probe override:
  `journey_pricing_direct_journey_label_completion_bound_unique_task_helper_enabled=True`,
  `journey_pricing_direct_journey_label_completion_bound_unique_route_helper_enabled=True`,
  `journey_pricing_direct_journey_label_completion_bound_time_buckets=10`, and
  `journey_pricing_direct_journey_label_completion_bound_energy_buckets=10`.
- Result file:
  `BPC_future/results/probe_standalone_unique_route_tranq10_09_20260606.csv`.
- Outcome: `TIME_LIMIT`, primal `203.102839`, no certificate dual, time
  `119.076670s`, root-only `nodes=1`, columns `476`.
- Ordinary heuristic/profile scans saw the helper flags, but only tiny pruning
  counts early in CG.  The late `exact_completion_bound_pre_exact_handoff` at
  `cg_iter=21` still built the full CB table, spent about `32.13s`, pruned
  `333503` labels, selected `18` true-RC negative journeys, and all selected
  journeys were replacements:
  `direct_label_harvest_selected_new_task_set_count=0`,
  `direct_label_harvest_selected_replacement_task_set_count=18`, and
  `active_changed_task_set_count=0`.

Decision:

- Keep the standalone helper code opt-in only.  It is exact-safe and compiled,
  but this probe does not justify enabling it by default.
- The dominant failure remains unchanged: expensive true-dual judge work is
  producing replacement-only inactive columns, so RMP degeneracy persists and
  the root certificate does not close inside the engineering time limit.

## 2026-06-06: Active-Support Replacement Repair And Patrol Escalation Do Not Fix `tranq10_09`

Context:

- The previous probes showed that final-judge harvests on
  `tranq10_09` mostly produce replacement columns for inactive task sets.
  A natural next hypothesis was that a cheap true-dual worker should repair
  the current LP active support before the heavy CB judge is invoked.

Implementation note:

- Added an opt-in active-support target selector for the existing
  replacement-repair worker:
  `journey_replacement_repair_target_active_task_sets_enabled`.
- Default behavior is unchanged.  The old recent-changed target path remains
  controlled by `journey_replacement_repair_target_recent_changed_task_sets_enabled`
  and defaults to `True`.
- While probing the helper-only path, fixed a bug in
  `_direct_sortie_partial_completion_bound_check`: the `route_finish`
  completion lookup now only calls `completion_bound.value(...)` when a full
  completion-bound table exists.  Unique-task / unique-route helper-only
  pruning remains allowed without a full CB table.

Probe 1: active-support repair with default pre-exact handoff

- Overrides:
  `journey_replacement_repair_enabled=True`,
  `journey_replacement_repair_target_active_task_sets_enabled=True`,
  `journey_replacement_repair_target_recent_changed_task_sets_enabled=False`,
  `journey_replacement_repair_time_limit=2.0`, and
  `journey_replacement_repair_final_reserve_time=8.0`.
- Result file:
  `BPC_future/results/probe_active_repair_tranq10_09_20260606.csv`.
- Outcome: `TIME_LIMIT`, primal `203.102839`, no dual certificate, time
  `119.073728s`, root-only `nodes=1`, columns `476`.
- Interpretation: the active repair worker did not run because
  `journey_certificate_completion_bound_pre_exact_handoff_enabled=True`
  caused the late iteration to hand directly to CB before the repair stage.

Probe 2: active-support repair with pre-exact handoff disabled

- Added override:
  `journey_certificate_completion_bound_pre_exact_handoff_enabled=False`.
- Result file:
  `BPC_future/results/probe_active_repair_no_prehandoff_tranq10_09_20260606.csv`.
- Outcome: `TIME_LIMIT`, primal `203.102839`, no dual certificate, time
  `119.077629s`, root-only `nodes=1`, columns `476`.
- The repair worker did run at `cg_iter=21` with `target_task_sets=2`, spent
  about `2.01s`, generated `9166` sequences, and returned no true-RC negative
  journeys:
  `direct_label_harvest_candidate_count=0`,
  `direct_label_harvest_selected_count=0`.
- Interpretation: this hard tail is not caused by cheap physical replacements
  of the current LP active task sets.  The hidden negatives are off-support.

Probe 3: replacement-only patrol escalates directly to CB

- Override:
  `journey_hidden_negative_patrol_replacement_only_escalates_to_cb=True`.
- Result file:
  `BPC_future/results/probe_patrol_replacement_escalates_tranq10_09_20260606.csv`.
- Outcome: `TIME_LIMIT`, primal `203.102839`, no dual certificate, time
  `119.178516s`, root-only `nodes=1`, columns `473`.
- At `cg_iter=13`, the patrol found `2` replacement-only negatives and
  escalated immediately to CB.  The CB retry then spent about `43.76s`, found
  many candidates (`direct_label_harvest_candidate_count=385`), selected
  `20` columns, but still only `3` were new task sets and none touched the
  active support:
  `active_changed_task_set_count=0`.

Decision:

- Do not enable active-support replacement repair by default.  Keep the
  selector and bug fix because they are exact-safe and tested, but the probe
  shows no benefit on the representative hard root.
- Do not enable
  `journey_hidden_negative_patrol_replacement_only_escalates_to_cb` by default.
  It pulls CB earlier and turns the judge into an expensive worker sooner.
- The current hard-root bottleneck is still off-support hidden negatives plus
  RMP degeneracy, not missing active-support physical replacements.

## 2026-06-06: Budget-Reserve Guard Is Exact-Safe But Does Not Solve 10-Task Tail

Context:

- A `tranq10_09` probe with
  `journey_certificate_completion_bound_after_retry_min_time=6.0` exposed a
  final-judge scheduling bug: with about `6.17s` wall-clock remaining and a
  configured `2.0s` reserve, the old helper still promoted the CB retry budget
  back to `6.0s`.  This consumed the reserve and could overrun the outer
  solver limit.
- The scheduler was changed so final CB viability is checked after subtracting
  the reserve.  A final judge is launched only when the post-reserve budget is
  at least the configured minimum.  This is exact-safe: skipped probes leave the
  node incomplete rather than producing a false certificate.

Validation:

- Compiled `BPC_future/solver/journey_driver.py` and
  `BPC_future/pricing/journey_pricing.py`.
- Passed:
  `test_direct_journey_label_completion_bound_prunes_expanded_label` and
  `test_direct_journey_completion_bound_reuses_resource_cache`.
- Focused probe
  `BPC_future/results/probe_cb_min6_budgetfix_tranq10_09_20260606.csv`:
  `TIME_LIMIT`, primal `203.102839`, no certificate dual, root-only `nodes=1`,
  columns `493`, solving time about `113.80s`.
- The last CB retries used post-reserve budgets:
  remaining `43.655806 -> pricing_time_limit 41.655806`, and
  remaining `23.930334 -> pricing_time_limit 21.930334`.  The previous bad
  pattern, `remaining ~= 6s` with `pricing_time_limit=6s`, disappeared.

Full 5/10 run after the guard:

- 5-task output:
  `BPC_future/results/all_tasks05_current_after_budgetfix_full_20260606.csv`.
  All `20/20` instances are `OPTIMAL`; average time `1.106549s`, max
  `2.118330s`.  Log audit found `20/20` OPTIMAL runs have a true-dual global
  `CERTIFIED_NO_NEGATIVE` certificate and `pricing_incomplete_nodes=0`.
- 10-task output:
  `BPC_future/results/all_tasks10_current_after_budgetfix_full_20260606.csv`.
  `14/20` instances are `OPTIMAL`; all `14/14` OPTIMAL runs passed the same
  log-level certificate audit.  Average over all 10-task instances is
  `75.298193s`; OPTIMAL average is `56.815265s`; `8` exact OPTIMAL instances
  still exceed the `60s` target.
- The six non-exact 10-task cases are:
  `apollo15_20km_tasks10_04_seed11055` with a partial branch-tree bound
  (`dual_bound=268.585633`, `pricing_incomplete_nodes=2`), and five root
  certificate failures with no official dual bound:
  `tranq10_01`, `tranq10_04`, `tranq10_06`, `tranq10_07`, and `tranq10_09`.

Decision:

- Keep the post-reserve final-judge guard.  It fixes a real scheduler bug and
  prevents wasting the last seconds on a probe that cannot certify.
- Do not treat this as a speed optimization.  It slightly improves time-limit
  hygiene but leaves the main 10-task bottleneck unchanged: hard roots still
  need stronger true-dual worker/judge behavior, and `apollo10_04` still needs
  branch-tree proof acceleration.

## 2026-06-06: Four More 10-Task Tail Probes Did Not Fix `tranq10_09`

Context:

- Representative hard root:
  `tranquillitatis_balmer_like_20km_tasks10_09_seed11144`.
- Baseline after the budget-reserve guard:
  `BPC_future/results/all_tasks10_current_after_budgetfix_full_20260606.csv`.
  The instance reaches primal `203.102839` early but remains root-incomplete,
  with no official dual bound.
- These probes were aimed at reducing repeated final-judge calls or letting
  learning provide better tail columns.  None should be promoted to default.

Probe 1: restore hidden-negative profile catalog seed

- Override / change tested:
  `journey_hidden_negative_profile_catalog_seed_enabled=True`.
- Result file:
  `BPC_future/results/probe_profile_seed_restored_tranq10_09_20260606.csv`.
- Outcome: `TIME_LIMIT`, primal `203.102839`, no dual certificate, root-only,
  columns `480`, wall time about `119.19s`.
- The seed path ran only a couple of times and seeded `5` journeys, but the
  tail concentrated into one very large CB retry:
  about `57.06s` profile time, `1,081,113` labels pruned by LB, `415,099`
  expanded-after-bound labels, and only `1` selected new task set.
- Decision: keep
  `journey_hidden_negative_profile_catalog_seed_enabled=False`.  In this
  current scheduler, seeding can pull work into an expensive judge call rather
  than improving the certificate.

Probe 2: allow one weak learning tail fallback column

- Override:
  `journey_learning_certificate_true_rc_fallback_max_kept_per_round=1`.
- Result file:
  `BPC_future/results/probe_learning_tail_fallback1_tranq10_09_20260606.csv`.
- Outcome: `TIME_LIMIT`, primal `203.102839`, no dual certificate, root-only,
  columns `495`, wall time about `118.69s`.
- Learning did add a weak true-RC replacement tail column at `cg_iter=16`
  (`best_true_rc ~= -2.004524`), but this increased worker activity and did not
  reduce certificate work.  The CB retries selected `20` columns with
  `selected_new=0`.
- Decision: keep the default
  `journey_learning_certificate_true_rc_fallback_max_kept_per_round=0`.
  Weak tail learning columns are valid columns, but in this hard root they do
  not move the RMP enough to justify the extra iterations.

Probe 3: reduce ordinary exact worker time limit to 12 seconds

- Override:
  `journey_pricing_time_limit=12.0`.
- Result file:
  `BPC_future/results/probe_worker_tlim12_tranq10_09_20260606.csv`.
- Outcome: `TIME_LIMIT`, primal `203.102839`, no dual certificate, root-only,
  columns `490`, wall time about `113.12s`.
- The run was slightly shorter, but still failed to certify.  Ordinary exact
  work remained expensive (`profile_time ~= 62.09s`, `dp_time ~= 18.91s`), and
  CB retries selected no new task sets.
- Decision: do not lower the default worker time limit.  It only changes the
  timeout shape; it does not solve the hidden-negative / proof-tail issue.

Probe 4: stop learning after a no-strong-column round

- Override:
  `journey_learning_stop_after_no_strong_round=True`.
- Result file:
  `BPC_future/results/probe_learning_stop_after_weak_tranq10_09_20260606.csv`.
- Outcome: `TIME_LIMIT`, primal `203.102839`, no dual certificate, root-only,
  columns `494`, wall time about `112.79s`.
- Learning filters dropped sharply (`19 -> 2` on this run), so this suppresses
  no-op learning work.  However, exact/CB proof work remained essentially the
  same, and CB selected no new task sets.
- Decision: do not enable by default.  The user requirement is to optimize
  learning, not to hide it.  This is a diagnostic suppression knob, not a real
  solution to the certificate tail.

Current conclusion:

- The hard-root bottleneck is not primarily caused by the profile seed flag,
  weak learning tail columns, an overly large ordinary exact worker time limit,
  or repeated no-op learning calls.
- `tranq10_09` remains a primal-solved but proof-incomplete root-tail case:
  the incumbent is reached early, then the RMP objective stays flat while duals
  keep oscillating and true-dual pricing fails to produce a final global
  certificate within the 120 second limit.
- The next promising work should strengthen the true-dual certificate path or
  the RMP tail stabilization itself, not add more local worker toggles.

## 2026-06-06: Completion-Bound Proof-Mode Probe Without Negative Early Return

Context:

- The default final completion-bound judge on hard `tranq10_09` still has
  negative-column early-return semantics.  Even with elapsed soft return
  disabled, it can return `INCOMPLETE / direct_label_partial_negative_journey`
  after collecting the configured number of negative columns.
- A probe tested whether making the final judge more proof-like would help:
  disable direct-label negative early return plus the CB hidden-negative and
  diverse-harvest early-return wrappers, so the direct-label search continues
  until exhaustion or the local budget limit.

Probe:

- Result file:
  `BPC_future/results/probe_cb_proofmode_noearly_tranq10_09_20260606.csv`.
- Overrides:
  `journey_pricing_direct_journey_label_early_return_negative=False`,
  `journey_certificate_completion_bound_hidden_negative_enabled=False`, and
  `journey_certificate_completion_bound_diverse_harvest_enabled=False`.
- Outcome: `TIME_LIMIT`, primal `203.102839`, no certificate dual, root-only,
  columns `473`, wall time about `119.17s`.
- The single CB retry at `cg_iter=13` ran until its local time limit:
  `reason=time_limit`, `exhausted=False`,
  `profile_generation_time ~= 42.80s`, `lb_pruned_labels=400088`,
  `expanded_labels_after_bound=376646`.
- It selected `30` true-RC negative journeys, but only `3` were new task sets
  and `27` were replacements.  No global certificate was reached.

Decision:

- Do not disable negative early return globally and do not convert all final
  CB calls into proof-mode by default.  It spends much more of the 120 second
  budget in one judge call and still returns a replacement-heavy batch.
- Keep the conceptual distinction: proof-mode is exact-safe, but on this hard
  root it is not a performance fix unless paired with a stronger bound or a
  candidate-generation change that produces substantially more new task-set
  directions before the local time limit.

## 2026-06-06: Branch Cross-Node Pricing Cache Does Not Solve `apollo10_04`

Context:

- The only non-root 10-task failure in the current full run is
  `apollo15_20km_tasks10_04_seed11055`.
- Root and several depth-1/depth-2 nodes can certify, but later branch nodes
  start with only a few seconds left and end as `profile_dp_incomplete`.
- The branch driver already has an opt-in cross-node pricing cache, so a probe
  tested whether sibling nodes can reuse enough physical pricing work to finish
  the branch proof.

Probe:

- Result file:
  `BPC_future/results/probe_branch_cross_node_cache_apollo10_04_20260606.csv`.
- Overrides:
  `journey_branch_pricing_cross_node_cache_enabled=True` and
  `journey_branch_pricing_cross_node_cache_max_entries=50000`.
- Outcome: `TIME_LIMIT`, primal `288.332462`, dual bound `268.585633`, gap
  `0.068486`, `nodes=9`, `pricing_incomplete_nodes=3`, wall time about
  `120.00s`.
- This did not improve the certificate chain.  Some node timings shifted, but
  depth-2/depth-3 nodes still ran out of final proof time.  The open-node proof
  issue remains.

Decision:

- Do not enable cross-node branch pricing cache by default based on this probe.
  It is exact-safe infrastructure, but it does not address the dominant branch
  proof bottleneck in the current 10-task failure.
- Future work for `apollo10_04` should focus on node scheduling / proof-budget
  allocation or a stronger final judge, not generic sibling cache reuse.

## 2026-06-06: Disabling Learning Does Not Fix The Hard Root

Context:

- The updated performance goal no longer requires learning to stay enabled, so
  a direct probe tested whether the GNN worker is a net runtime burden on
  hard `tranq10_09`.

Probe:

- Result file:
  `BPC_future/results/probe_learning_off_tranq10_09_20260606.csv`.
- Overrides:
  `journey_learning_required=False` and `journey_learning_enabled=False`.
- Outcome: `TIME_LIMIT`, primal `203.102839`, no certificate dual, root-only,
  columns `492`, wall time about `119.42s`.
- Removing learning eliminated heuristic learning calls, but the saved time was
  absorbed by ordinary exact/profile retry and completion-bound work:
  ordinary exact/profile still took about `39.96s` profile generation plus
  `14.47s` profile DP; exact retry took about `17.36s`; two CB retries took
  about `42.40s` and selected `20` replacement-only columns with `0` new task
  sets.

Decision:

- Do not disable learning by default.  It is not the cause of the current
  `tranq10_09` certificate failure.
- The main bottleneck remains true-dual tail proof and inactive
  replacement-heavy column batches.

## 2026-06-07: Full 5/10 Verification With True-Dual Certificate Audit

Context:

- The current target time limits are 120 seconds for all 5-task and 10-task
  instances.  A run status of `OPTIMAL` is not sufficient by itself: an exact
  journey result must have a true-dual final certificate from the direct-label
  judge, not a profile/local no-column result.
- The audit criterion used here is:
  `pricing_state=CERTIFIED_NO_NEGATIVE`,
  `global_certificate=True`,
  `pricing_dual_source=scip_certificate`, and no final incomplete pricing
  nodes.

Run:

- 5-task result file:
  `BPC_future/results/all_tasks05_verify_20260607.csv`.
- 10-task result file:
  `BPC_future/results/all_tasks10_verify_20260607.csv`.

Outcome:

- 5-task: 20/20 are exact-certified.  Average solving time is about
  `0.955s`; maximum is about `1.941s`.  This meets the current 10 second
  exact target.
- 10-task: 13/20 are exact-certified.  Average time over all 20 rows is about
  `77.024s`; average over the 13 exact-certified rows is about `54.267s`;
  the slowest exact-certified row is about `104.271s`.
- Seven 10-task rows are not exact certificates because they end in
  `TIME_LIMIT / INCOMPLETE_LIMIT`:
  `apollo15_20km_tasks10_04_seed11055`,
  `tranquillitatis_balmer_like_20km_tasks10_01_seed11000`,
  `tranquillitatis_balmer_like_20km_tasks10_04_seed11054`,
  `tranquillitatis_balmer_like_20km_tasks10_05_seed11072`,
  `tranquillitatis_balmer_like_20km_tasks10_06_seed11090`,
  `tranquillitatis_balmer_like_20km_tasks10_07_seed11108`, and
  `tranquillitatis_balmer_like_20km_tasks10_09_seed11144`.
- Eight 10-task rows are exact-certified but still exceed the 60 second target:
  Apollo10 seeds `11073`, `11109`, `11127`, `11145`; Tranquillitatis10 seeds
  `11018`, `11036`, `11126`, `11162`.

Diagnosis:

- The 5-task layer is no longer the bottleneck.
- The 10-task hard-root failures are still proof failures, not merely primal
  failures.  The current funnel can often reach a good incumbent, but the
  true-dual final judge remains too expensive to close the certificate within
  120 seconds on the hard Tranquillitatis roots.
- Learning is active in the current configuration, but it is not breaking the
  hard tail.  It should remain a worker/guide and must not be treated as a
  certificate source.
- The most plausible next unexplored direction is improving physical
  representatives earlier, before final certificate pricing.  Recent hard-root
  logs show completion-bound batches are heavily replacement-oriented and add
  few or zero new task sets, which suggests the RMP already knows many task
  sets but has weak physical representatives for them.

Decision:

- Do not repeat the already failed toggles listed above unless a new audit gives
  a different mechanism.
- Next probe should be small and evidence-driven: increase initial journey pool
  / source-trip representative coverage on one hard 10-task root and compare
  whether completion-bound replacement pressure, final incomplete status, and
  wall time improve.  If this only bloats the RMP or columns without improving
  the certificate, record it as another failed path and move to a more targeted
  representative-optimization worker.

## 2026-06-07: Larger Initial Representative Pool Does Not Fix Hard Root

Context:

- A hard-root probe tested whether `tranq10_09` is failing mainly because the
  initial journey pool and source-trip representative coverage are too narrow.
- This was a config-only diagnostic.  It should not be promoted to the default
  unless it improves the certificate chain without bloating the RMP.

Probe:

- Result file:
  `BPC_future/results/probe_initial_reps_tranq10_09_20260607.csv`.
- Overrides:
  `initial_composite_seed_max_trips=800`,
  `journey_initial_source_trip_limit=2500`,
  `journey_initial_max_columns=6000`, and
  `journey_pool_max_extensions_per_prefix=80`.
- Baseline row for the same instance in the current full run:
  `BPC_future/results/all_tasks10_verify_20260607.csv`.

Outcome:

- Probe outcome: `TIME_LIMIT`, primal `203.102839`, no certificate dual,
  root-only, wall time about `119.241s`, columns `510`.
- Baseline current full-run outcome for the same instance:
  `TIME_LIMIT`, primal `203.102839`, no certificate dual, root-only, wall time
  about `119.092s`, columns `492`.
- The completion-bound harvest still selected only replacement task sets:
  `harvest_candidate_new_task_set_count=0` and
  `harvest_selected_new_task_set_count=0`.
- The first logged CB harvest in the probe selected 10 replacement task sets,
  with `harvest_candidate_negative_count=95`,
  `harvest_selected_replacement_task_set_count=10`, and worst selected true RC
  about `-0.190`.  The analogous baseline CB harvest selected 10 replacement
  task sets from 130 negative candidates, also with zero new task sets.

Decision:

- Do not increase the initial pool / source-trip limits by default.  This
  makes the RMP slightly larger and does not close the hard-root certificate.
- The stronger diagnosis is that CB is being used to discover replacement
  physical representatives for already-known task sets.  The existing log
  fields show `profile_replacement_true_rc_materialization_max_candidates=0`,
  so the profile worker is not currently doing this repair before final judge.
- Next promising code/config path: inspect the existing profile replacement
  materialization worker and test a small, bounded, worker-only activation
  before final certificate pricing.  It must return true-RC checked columns and
  must never certify no-column.

## 2026-06-07: Profile Replacement Materialization Generates Candidates But Does Not Close Tail

Context:

- The previous probe showed that simple initial-pool expansion does not fix
  hard `tranq10_09`.
- Logs also showed the profile replacement materialization worker was disabled
  by `profile_replacement_true_rc_materialization_max_candidates=0`, while CB
  kept returning replacement-only negative columns.
- A bounded worker-only probe enabled this existing profile materialization path
  late in pricing.  This is exact-safe as a worker because candidates still go
  through true-RC/nonduplicate selection and do not certify no-column.

Probe:

- Result file:
  `BPC_future/results/probe_profile_replacement_materialization_tranq10_09_20260607.csv`.
- Overrides:
  `journey_pricing_late_profile_replacement_true_rc_materialization_slack=2.0`,
  `journey_pricing_late_profile_replacement_true_rc_materialization_max_candidates=64`,
  and `journey_pricing_profile_materialization_feasibility_filter_enabled=True`.

Outcome:

- Outcome: `TIME_LIMIT`, primal `203.102839`, no certificate dual, root-only,
  wall time about `119.086s`, columns `495`.
- Compared with the current full-run baseline for the same instance
  (`119.092s`, columns `492`), this does not improve the certificate.
- The worker did trigger: aggregate
  `profile_replacement_materialization_candidate_count=158`,
  `profile_replacement_materialization_selected_for_scan_count=158`, and
  `profile_replacement_materialization_selected_candidate_count=158`.
- However, many late rounds ended as `weak_negative_journeys_filtered`, and the
  final state remained incomplete.  Generated sequences and evaluated timed
  trips increased versus the baseline, while CB still selected replacement-only
  batches with `harvest_selected_new_task_set_count=0`.

Decision:

- Do not enable late profile replacement materialization by default in this
  form.  It finds candidate replacements, but they are too weak/noisy to break
  the tail and they add pricing work.
- The hard-root issue is narrower than "profile never repairs replacements":
  it needs either stronger ranking of replacement representatives, a cheaper
  fixed-task-set representative optimizer, or an earlier final-judge handoff
  that does not spend the last seconds cycling through weak filtered workers.

## 2026-06-07: Lowering CB After-Retry Min Time Alone Is Not A Tail Fix

Context:

- The current 10-task config differs from the repository baseline by changing
  `journey_certificate_completion_bound_after_retry_min_time` from `1.0` to
  `6.0`.
- This was a plausible regression source because hard roots can spend their
  final seconds in profile/learning incomplete states instead of giving the
  true-dual final judge enough time.

Probe:

- Result file:
  `BPC_future/results/probe_cb_min_time_1_tranq10_09_20260607.csv`.
- Override:
  `journey_certificate_completion_bound_after_retry_min_time=1.0`.

Outcome:

- Outcome: `TIME_LIMIT`, primal `203.102839`, no certificate dual, root-only,
  wall time about `119.147s`, columns `495`.
- The last events are essentially the same as the current baseline:
  a CB call at `cg_iter=23` finds 5 replacement-only columns, then the final
  iteration ends in `profile_dp_incomplete` under `scip_learning_certificate`.
- Aggregate CB harvest stays at 26 selected columns, zero new task sets, and
  about 407 negative candidates.

Decision:

- Do not treat the `after_retry_min_time` change as the main root cause.
  Lowering it alone does not recover the certificate on `tranq10_09`.
- The persistent failure signature remains replacement-only CB harvest with no
  new task-set directions.  Continue toward a stronger fixed-task-set physical
  representative repair path rather than more timing threshold probes.

## 2026-06-07: Existing Profile Repair Worker Also Does Not Fix Hard Root

Context:

- The direct-label replacement repair path is still a reduced-cost search and
  had already failed in earlier probes.
- The profile repair worker looked cheaper and closer to a worker-only repair
  layer, so it was tested on the same hard root.

Probe:

- Result file:
  `BPC_future/results/probe_profile_repair_tranq10_09_20260607.csv`.
- Override:
  `journey_profile_repair_enabled=True`.

Outcome:

- Outcome: `TIME_LIMIT`, primal `203.102839`, no certificate dual, root-only,
  wall time about `119.080s`, columns `495`.
- The worker ran twice, at `cg_iter=17` and `cg_iter=23`, each with a 2 second
  budget.  Both calls ended as `INCOMPLETE_LIMIT / profile_dp_incomplete` and
  added no journeys.
- The final CB call still returned replacement-only columns:
  aggregate `harvest_selected_count=24`,
  `harvest_selected_new_task_set_count=0`, and
  `harvest_candidate_negative_count=392`.

Decision:

- Do not enable `journey_profile_repair_enabled` by default.  It consumes final
  time without reducing the replacement-only CB tail.
- The existing repair workers are still too generic.  A useful next repair must
  be more targeted than "run another profile/direct-label pricing pass": it
  should optimize physical representatives for selected known task sets, or it
  should be skipped entirely.

## 2026-06-07: Same-Dual No-Column Unlock Before CB Is Not A Tail Breaker

Context:

- Fresh 10-task logs showed completion-bound final judge calls acting as an
  expensive unlocker: ordinary/profile pricing reported local no-column, then
  CB found mostly replacement-only true-dual columns, after which ordinary
  exact/profile sometimes found more columns.
- A temporary worker was tested between ordinary/profile local no-column and
  the CB final judge.  It reused the existing same-dual direct-label supplement
  with resource coarsening, true-dual pricing, and no certificate capability.
  The goal was to replace a tens-of-seconds CB worker call with a subsecond
  replacement/new-column unlock.

Probe:

- Result file:
  `BPC_future/results/probe_same_dual_no_column_unlock_tranq10_09_20260607.csv`.
- Instance:
  `tranquillitatis_balmer_like_20km_tasks10_09_seed11144`.
- Temporary override:
  `journey_same_dual_no_column_unlock_enabled=True`.

Outcome:

- Result stayed `TIME_LIMIT`, primal `203.102839`, no dual bound, root-only,
  wall time about `119.122s`, columns `497`.
- The unlock triggered three times.  It added columns cheaply, including at
  `cg_iter=11` (`4` replacement-only), `cg_iter=18` (`1` new and `3`
  replacement), and one final trigger at `cg_iter=27` that found no addable
  unlock before CB.
- Across all same-dual supplement calls in the probe, the worker selected `38`
  columns but only `3` new task-set directions and `35` replacements.  None
  touched active support in the logged additions.
- CB calls were reduced to one, but that final CB still spent about `31.2s`,
  selected `5` replacement-only columns, and did not certify the root before
  time limit.

Decision:

- Do not add or enable a no-column same-dual unlock before CB.  It mostly
  converts expensive CB replacement columns into cheap replacement columns, but
  still inflates the RMP and does not produce the active-support or certificate
  movement needed on the hard root.
- The temporary code was removed after the probe.  Future work should not
  revisit this as another generic pre-CB replacement worker; the next useful
  direction must either strengthen the final proof itself or generate columns
  with demonstrable active-support/new-task-set impact.

## 2026-06-07: Old 30-Second 10-Task Runs Are Not Valid Exact Baselines

Context:

- Several 2026-06-04 result files report much faster 10-task performance, for
  example:
  `all_tasks10_learning_min2_120s_full_20260604.csv`,
  `all_tasks10_learning_threshold10_isolated_120s_20260604.csv`,
  `all_tasks10_learning_nostrong_stop_120s_full_20260604.csv`, and
  `mainline_required_tasks10_all_prewarm_20260604.csv`.
- These files have 20/20 `OPTIMAL` rows and average wall times around
  28-30 seconds, which looks close to the target.

Audit:

- Rechecked their available JSONL logs using the current exactness criterion:
  a true-dual journey certificate must show
  `pricing_state=CERTIFIED_NO_NEGATIVE`,
  `global_certificate=True`, and
  `pricing_dual_source=scip_certificate`.
- The audited logs do not contain such certificate events.  They appear to come
  from the older pricing-status semantics, before profile/local no-column was
  separated from global journey certificate no-column.

Decision:

- Do not use those 30-second runs as proof that the current exact solver has
  regressed from a valid exact baseline.  They are useful historical speed
  references, but not exactness evidence under the current certificate chain.
- Current valid baseline is the 2026-06-07 true-dual certificate audit:
  5-task 20/20 exact, 10-task 13/20 exact.
- The performance gap is real, but it is the cost of restoring correct
  certificate semantics.  Optimizations must preserve the repaired semantics,
  not chase the old local-no-column `OPTIMAL` behavior.

## 2026-06-07: Fixed Task-Set Representative Repair Is Safe But Not The Tail Breaker

Context:

- A new opt-in worker was added to test a narrower replacement hypothesis:
  instead of running another generic profile/direct-label pricing pass, optimize
  physical representatives for already-known small task sets.
- The first version is deliberately conservative:
  root-only by default, disabled by default, single-sortie only, small task sets
  only, true-dual RC checked, and never certificate-capable.

Implementation:

- Code path:
  `_price_fixed_task_set_representatives` in
  `BPC_future/solver/journey_driver.py`.
- It is inserted before generic replacement repair / final CB in the node-loop
  funnel, and it is enabled only by
  `journey_fixed_task_set_repair_enabled=True`.
- Tests:
  `test_fixed_task_set_repair_targets_and_gate_are_worker_only` and
  `test_fixed_task_set_repair_finds_same_task_set_cheaper_true_negative`.
- Validation command run:
  `PYTHONDONTWRITEBYTECODE=1 python -m unittest ...test_fixed_task_set_repair...`
  plus `python -m compileall -q BPC_future/solver/journey_driver.py
  BPC_future/tests/test_bpc_future.py`.

Probes on hard `tranq10_09`:

- `probe_fixed_task_set_repair_nodeloop_tranq10_09_20260607.csv`:
  target active/recent small sets, one path option per leg.  Outcome
  `TIME_LIMIT`, primal `203.102839`, columns `491`.  The worker ran and found
  2 true-negative replacement columns at `cg_iter=17`; both were inactive.
- `probe_fixed_task_set_repair_options2_tranq10_09_20260607.csv`:
  same target policy, two path options per leg and up to 16 option combinations.
  Outcome `TIME_LIMIT`, columns `491`.  It found the same 2 replacements, with
  much more trip evaluation, so non-default path options are not the missing
  mechanism here.
- `probe_fixed_task_set_repair_poolwide_tranq10_09_20260607.csv`:
  disable active/recent targets and scan up to 256 pool-selected small task
  sets by current true RC.  Outcome `TIME_LIMIT`, columns `491`.  The worker
  found 10 true-negative replacement columns across `cg_iter=17` and `20`, all
  inactive.  Final CB still returned replacement-only batches with
  `harvest_selected_new_task_set_count=0`.

Decision:

- Keep the worker default-off.  It is exact-safe and cheap enough for targeted
  experiments, but it does not solve the hard root tail.
- This is strong evidence that "more replacement-only physical representatives"
  is not sufficient.  The next useful direction should bias toward columns that
  touch the active LP support or produce genuinely new task-set directions, or
  should strengthen the true-dual final judge itself.

Follow-up wide-budget probe:

- Probe:
  `BPC_future/results/probe_fixed_task_set_repair_wide5_tranq10_09_20260607.csv`.
- Overrides widened the existing opt-in repair worker:
  `journey_fixed_task_set_repair_time_limit=5.0`,
  `journey_fixed_task_set_repair_max_target_task_sets=1024`,
  recent/active targeting disabled, pool-best targeting enabled, and up to
  `64` returned journeys.
- Outcome stayed `TIME_LIMIT`, primal `203.102839`, no dual bound,
  `columns=498`.
- The worker was cheap per call and did find replacement columns:
  at `cg_iter=11` it found `5`, at `13` found `2`, at `15` found `2`, and at
  `19` found `1`.  Every added column was replacement-only and inactive
  (`active_changed_task_set_count=0`).
- Completion-bound still had to run and still returned replacement-heavy
  batches: at `cg_iter=17` it selected `1` new and `9` replacement task sets;
  at `cg_iter=20` it timed out after selecting `4` replacement-only columns.

Decision:

- Do not keep widening the fixed-task-set repair budget.  The broader probe
  confirms the same failure mode as the narrow probe: the worker can improve
  physical representatives, but those columns do not alter active LP support
  and do not shorten the certificate tail.

## 2026-06-07: Current Full 5/10 Audit And Suffix-Only CB Cache Reprobe

Context:

- A fresh current-mainline full 5/10 run was performed with the engineering
  `120s` limit.  Exactness was audited from JSONL logs, not only from CSV
  status.
- The exact audit condition remains:
  `pricing_state=CERTIFIED_NO_NEGATIVE`, `global_certificate=True`,
  `pricing_dual_source=scip_certificate`, and final
  `pricing_incomplete_nodes=0`.

Full run:

- 5-task result file:
  `BPC_future/results/all_tasks05_current_20260607_060341.csv`.
  Outcome: `20/20` exact-certified `OPTIMAL`, average `0.941879s`, maximum
  `1.918348s`.
- 10-task result file:
  `BPC_future/results/all_tasks10_current_20260607_060341.csv`.
  Outcome: `13/20` exact-certified `OPTIMAL`, average `73.251168s`, maximum
  `119.791719s`; `13` rows exceed the `60s` final target.
- The seven non-exact 10-task rows are:
  `apollo15_20km_tasks10_04_seed11055`,
  `tranquillitatis_balmer_like_20km_tasks10_01_seed11000`,
  `tranquillitatis_balmer_like_20km_tasks10_04_seed11054`,
  `tranquillitatis_balmer_like_20km_tasks10_06_seed11090`,
  `tranquillitatis_balmer_like_20km_tasks10_07_seed11108`,
  `tranquillitatis_balmer_like_20km_tasks10_09_seed11144`, and
  `tranquillitatis_balmer_like_20km_tasks10_10_seed11162`.

Suffix-only completion-bound cache reprobe:

- Motivation: an older suffix-only cache probe was inconclusive because the
  final judge did not receive enough meaningful budget.  The current
  `tranq10_06` baseline has one large root completion-bound final probe:
  about `67.50s` of direct-label search, no negative columns, and no
  certificate, so it is a better test.
- Incorrect first override:
  `journey_pricing_direct_journey_label_next_sortie_cache_enabled=True`.
  This did not affect the certificate path; the completion-bound retry mode
  still logged `completion_bound_next_sortie_cache=False`, with zero
  cache hits/misses.  Do not use this key when testing certificate CB cache.
- Correct second override:
  `journey_certificate_completion_bound_partial_pruning_enabled=False` and
  `journey_certificate_completion_bound_next_sortie_cache_enabled=True`.
  Result file:
  `BPC_future/results/probe_cb_suffix_cache2_current_tranq10_06_20260607.csv`.
- Outcome stayed `TIME_LIMIT`, primal `196.791797`, no dual bound, root-only.
  The CB call did use the cache path (`completion_bound_next_sortie_cache=True`)
  but was slower overall:
  baseline CB around `67.50s`, suffix-cache CB around `69.79s`.
- Work shifted rather than disappeared:
  generated sequences fell from about `1.51M` to `0.47M`, and label expansion
  fell from about `2.21M` to `800`, but timed-trip evaluations rose from about
  `124k` to `601k`.  The cache path had only one miss and no hits, so disabling
  partial pruning removed too much early pruning for this final judge.

Decision:

- Do not enable suffix-only completion-bound caching by default.  For the
  current hard no-negative root proof, parent-specific partial pruning is more
  valuable than the next-sortie cache.
- If this direction is revisited, it needs a new cache that preserves
  parent-label partial completion pruning, not the existing coarse
  suffix-only profile cache.

## 2026-06-07: Unique-Route Future-Suffix Exact First Step Is Too Expensive

Context:

- The current completion-bound stats on hard root cases show many prunes from
  `lb_suffix_pruned_unique_route_winner`, so it was tempting to extend the
  existing exact-first-step tightening from partial routes to
  `_UniqueRouteCompletionLowerBound.future_value()`.
- The attempted change made the first future sortie from depot use exact
  `current_time` before falling back to the bucketed route DP.  It was
  proof-safe because it only took the max of two optimistic lower bounds.

Probe:

- Instance:
  `tranquillitatis_balmer_like_20km_tasks10_06_seed11090`.
- Baseline from `all_tasks10_20260607_rerun_exactcheck.csv`:
  `OPTIMAL`, `114.617292s`, one root final completion-bound proof.
- First implementation:
  `BPC_future/results/probe_future_exactfirst_tranq10_06_20260607.csv`.
  Outcome stayed `OPTIMAL` but slowed to `117.012617s`.
- Cached implementation:
  `BPC_future/results/probe_future_exactfirst_cache_tranq10_06_20260607.csv`.
  Outcome regressed to `TIME_LIMIT`, primal `196.791797`, no dual certificate.

Diagnostics:

- The non-cached version did prune more suffix labels and reduced some search
  counters:
  generated sequences fell from about `2.50M` to `2.43M`, evaluated timed
  trips from about `134k` to `70k`, and expanded labels from about `670k` to
  `538k`.
- Despite that, wall time increased.  The added exact future-suffix calls cost
  more than the saved search on this hard no-negative proof.

Decision:

- The code and test change were reverted.  Do not enable future-suffix
  exact-first-step under the existing
  `journey_certificate_completion_bound_unique_route_exact_first_step_enabled`
  flag.
- If revisited, it must be a separate opt-in flag with a cheaper monotone cache
  or a selective trigger.  Do not fold it into the current mainline exact-first
  partial-route bound.

## 2026-06-08: 20-Task Probe Stopped on Final-Judge State Budget, Not Wall Clock

Context:

- Two 20-task root-tail-zero probes were launched with an outer `--time-limit
  3600`, but both ended as `TIME_LIMIT` far earlier:
  `apollo15_20km_tasks20_02_seed21018` at about `965.70s` and
  `tranquillitatis_balmer_like_20km_tasks20_01_seed21000` at about `256.62s`.
- The CSV had incumbent primal values but `dual_bound=None` and `gap=None`, so
  neither run had an official no-negative certificate.

Diagnosis:

- The last root-node pricing path was:
  ordinary exact and retry found only weak/filtered negatives, hidden-negative
  patrol hit its small patrol `time_limit`, and the completion-bound final judge
  returned `INCOMPLETE` with reason `direct_label_partial_state_budget`.
- `journey_driver` maps any `PRICING_INCOMPLETE` node to `search_incomplete`,
  and the final solve status is then reported as `TIME_LIMIT` even when the
  wall-clock deadline has not expired.
- The 20-task config still used smoke-level final-judge budgets:
  `max_sequences=120000`, `max_dp_states=120000`,
  `partial_max_states=50000`.  That was too small for a 20-task proof probe.

Fix:

- Freeze the current 5/10 exact-safe baseline separately in
  `docs/frozen_5_10_mainline_20260608.md` and lock its config/model hashes in
  tests before changing 20-task settings.
- Raise only the 20-task completion-bound proof budgets to
  `max_sequences=1500000`, `max_dp_states=500000`,
  `partial_max_states=1500000`, with an exact-safe escalation retry budget of
  `3000000/1000000/3000000` when the final judge hits proof-state budgets while
  enough outer time remains.

Decision:

- Do not relax the official certificate rule.  `OPTIMAL` still requires the
  true-dual direct-label completion-bound final judge to prove no negative
  journey or return exact negative columns.
- Do not move these larger 20-task budgets into the frozen 5/10 configs unless
  the frozen benchmark lock is intentionally updated.

## 2026-06-08: Flat-Weak Replacement Repair Did Not Improve 20-Task Root Tail

Context:

- Existing logs showed that hard 20-task roots add many negative columns whose
  task sets do not intersect the current active support.  On
  `tranquillitatis_balmer_like_20km_tasks20_01_seed21000`, the active-changed
  ratio was only about `3.5%` in the target-200 probe.
- A conservative worker-only experiment added an opt-in
  `journey_replacement_repair_after_flat_weak_enabled` path.  It reused the
  existing direct-label replacement-repair worker after flat/weak ordinary
  exact additions.  The path was certificate-safe because no-column results
  stayed worker-local and only the final completion-bound judge could certify.

Probe:

- Config experiment: enable
  `journey_certificate_flat_weak_column_pressure_enabled`,
  `journey_replacement_repair_enabled`, and
  `journey_replacement_repair_after_flat_weak_enabled` for the 20-task config.
- Instance:
  `tranquillitatis_balmer_like_20km_tasks20_01_seed21000`.
- Result:
  `BPC_future/results/probe_target200_tranq20_01_flatweak_repair_20260608.csv`
  ended `TIME_LIMIT` at `94.228310s`, primal `387.429624`, no dual certificate.

Diagnosis:

- The repair trigger fired only once at `cg_iter=3`; the repair worker spent its
  `4.0s` budget and returned no columns because candidate task sets were
  dominated.
- The run still produced mostly inactive-only additions:
  `50` changed-inactive-only events versus `4` active-replacement events.
- It failed early at `cg_iter=54` with `weak_negative_journeys_filtered` from
  ordinary exact and retry, before reaching a valid final certificate path.

Decision:

- Keep the helper code opt-in for future controlled probes, but leave
  `journey_replacement_repair_after_flat_weak_enabled=False` and
  `journey_replacement_repair_enabled=False` in the 20-task default config.
- Do not promote this path to default.  The next useful direction is to fix
  ordinary profile-worker batching or weak-negative handling before the final
  judge, not to add an early replacement-repair sidecar.

## 2026-06-08: Profile True-RC Scan Widening Is Not the 20-Task Root-Tail Fix

Context:

- A new diagnostic split was added for profile materialization failures:
  `profile_selected_unmaterialized_candidate_count`,
  `profile_weak_filtered_materialized_count`,
  `profile_weak_filtered_best_rough_rc`,
  `profile_weak_filtered_best_true_rc`,
  `profile_weak_filtered_max_true_minus_rough`, and
  `profile_weak_filtered_max_true_minus_rough_mask`.
- On `tranquillitatis_balmer_like_20km_tasks20_01_seed21000`, the hard tail is
  not caused by non-materializable profile combinations.  The selected profile
  candidates materialize, but true reduced-cost rescoring turns many rough
  negatives into positive columns.

Probe results:

- Baseline-style diagnostic run reached `cg_iter=59` with `48` weak-filtered
  materialized candidates, best rough RC about `-13.825467`, best true RC about
  `+1.374968`, and max `true - rough` gap about `26.138630`.
- Setting late `profile_true_rc_candidate_scan_factor=4` and cap `192` did not
  widen the effective selected candidate count: streaming/profile DP still
  stopped at `48` candidates because `early_return_negative_min_count` was
  still `48`.  It finished `TIME_LIMIT` at `220.580979s`, primal `383.763369`.
- Raising late early-return and streaming negative batches to `192` did widen
  the candidate universe and found more true negative columns, but it spent too
  much time inside profile DP.  The same instance finished `TIME_LIMIT` at
  `220.182908s`, primal `385.878303`, with large DP times such as `34.371205s`
  and `33.498948s` in tail exact calls.
- Enabling only `journey_certificate_flat_weak_column_pressure_enabled` was also
  negative: `certificate_flat_rounds` stayed `0`, so the gate did not trigger a
  useful completion-bound path.  The run stopped early at `88.017025s`, primal
  `387.429624`, reason `weak_negative_journeys_filtered`.

Diagnosis:

- The profile-worker rough objective is a ranking heuristic in the tail, not a
  reliable proxy for true journey reduced cost.  Large rough-negative batches
  can be systematically positive under true-RC rescoring.
- Increasing only the true-RC scan factor is ineffective while streaming
  early-return stops after `48` unique-mask rough candidates.
- Increasing the early-return target enough to expose deeper candidates is
  exact-safe but too expensive and still mostly adds inactive-only task sets.
- The useful tail columns in the scan-factor run came from completion-bound
  direct-label harvest: at `cg_iter=59`, `exact_completion_bound_retry` found
  `10` columns including an active replacement task set.

Decision:

- Do not promote late profile true-RC scan widening or batch `192` to default.
- Do not re-enable flat-weak pressure by itself; it does not fire when flat
  rounds are not accumulating.
- The next promising direction is an exact-safe, budgeted completion-bound
  harvest trigger for root-tail active-support repair, rather than wider
  ordinary profile-DP scanning.
