# P0V5 QG2 V2 implementation-contract audit

Audit time: 2026-08-01T21:24:50+08:00. This is an implementation audit,
not performance evidence. Outcome-dependent gates remain pending.

| Contract | Status | Authoritative evidence |
|---|---|---|
| Intervention occurs only after the V5 midpoint and before the P0V4 fallback | PASS | `native_bidirectional_hybrid.py` constructs the fallback context, records the pre-action snapshot, calls the fail-closed QG2 runtime, and then invokes the unchanged fallback backend. |
| Scale 5/10/20 bypass before model import | PASS | `QG2_ALLOWED_SCALES={30,50}` and `prepare_qg2_request_from_environment` returns literal no-op before manifest/model loading; covered by `test_scale20_bypasses_qg2_before_manifest_or_model_load`. |
| One inference per pricing request, no per-label PyTorch call | PASS | Python produces node/arc potentials and 15 fixed coefficients once; Native computes the scalar label priority during queue insertion. |
| Queue key is terminal, RC bucket, descending guidance, exact partial RC, creation ID | PASS | `GreaterCachedKey` and `add_new_unprocessed_label` implement this order; `test_qg2_reorders_only_within_rc_buckets` verifies a real reorder without universe change. |
| Guidance only reorders within the same RC bucket | PASS | The RC bucket precedes guidance in the comparator. The 500-case Q0/QG2 randomized differential compares exhaustive status and the complete reduced-cost multiset. |
| Label-state schema has the frozen 15 features | PASS | Native `label_state_features` contains visit/sortie ratios, depot state, time/horizon, demand/energy/shadow, task/cut/positive-dual progress, and signed-log partial RC. Build info reports schema v1 and feature count 15. |
| No per-label embedding and State remains 176 B | PASS | Native stores only scalar cached priority keys; build info and CTest assert `label_state_bytes=176`. |
| Literal Q0 container remains the non-activated path | PASS | Q0 uses the original `unprocessed_q0_` container directly; every runtime exception/veto restores `proof_queue_policy_id=Q0`, `guidance_mode=off`, and no hints. |
| OOD/hash/NaN/zero/low-confidence fail closed | PASS | Runtime validates manifest, engine, exact action policy, checkpoint, training hash, feature envelope, finite outputs, nonzero potentials, and calibration thresholds before returning QG2. |
| Guidance cannot filter, prune, change dominance/bounds/RC, or certify | PASS | Guidance is installed only as ordering hints; Native randomized differential confirms identical exact universes, while snapshot/replay manifests declare zero certificate authority. |
| Active columns, task-set incidence, round, prior proof, dual delta, branch/cut and V5 midpoint are honest pre-action features | PASS | Snapshot v2 binds active semantic signatures/task sets and true-dual branch/cut context; missing trajectory values have explicit masks rather than zero imputation. |
| Learning target is Master-ready admission, not first raw negative | PASS | Replay objective is `min_time_to_master_ready_frozen_batch`; supervision uses ancestors of frozen-selector-selected Master-ready routes and fails closed without complete Master/witness mapping. |
| TIMEOUT/MEMORY_LIMIT/FRONTIER_LIMIT and zero-addable cases fail closed | PASS | Incomplete resource outcomes are right-censored; zero-addable admission batches are rejected. These cases are covered in the 62-test Python suite. |
| Random/QD1/QB1/QO2 are development-only arms | PASS | The bounded Oracle owns these arms; the deployable manifest requires model kind GAT and runtime action is only Q0 or QG2. |
| Clean-v2 snapshot binding | IN PROGRESS | First five completed scale30 contexts passed the strict index with `excluded_count=0`, source engine `0389484e5f5623f2`, and exact action-policy hash `9dcedb...7406ca`. The first six observed contexts span rounds 19--58, 1008--3531 active columns, dual L1 deltas 0.078--0.679, and V5 midpoint walls 0.689--1.310 s. |
| Bounded QO2 Oracle scale30/50 gates | PENDING | Must wait for the frozen clean-v2 collection and bounded real-tree supplement. No QO2 outcome has been promoted. |
| Linear/MLP/TinyGAT comparison and calibration | PENDING | Controller is fail-closed behind the Oracle pass. |
| Heldout replay, development E2E, formal full20 | PENDING | Frozen controllers exist and are waiting on upstream gates. |
| Independent candidate freeze | PENDING | Finalizer requires 16/16 pre-freeze checks and then 17/17 final checks; production switching is disabled. |

Current automated evidence: Python 62/62, Native CTest 2/2, 500 randomized
Q0/QG2 exact differentials, and clean diff checks.
