# B4.1 Stage A 20-scale closure audit

## Boundary

- This audit combines a full 20-scale 8-round run with a 16-round recheck of every failed 8-round instance.
- It is evidence that all previously failed 20-scale B3B/B4V2 rows close under the new 16-round default.
- It is not a single full-r16 replay; that remains the stronger final regression artifact.

## Evidence

- full 8-round rows: `runs/b4_1_true_dual_proof_tail_stage_a_20_full_b3b_b4v2/b4_1_rows.csv`
- failed-subset 16-round rows: `runs/b4_1_true_dual_proof_tail_stage_a_20_failed_r16_b3b_b4v2/b4_1_rows.csv`

## Counts

- full 8-round B3B/B4V2: 9/20 and 9/20 BPC_TREE_OPTIMAL.
- failed-subset 16-round B3B/B4V2: 11/11 and 11/11 BPC_TREE_OPTIMAL.
- combined closure audit rows: 40/40 closed = `True`.

## Status Counts

- `closed_after_16_round_recheck`: 22
- `closed_at_8_rounds`: 18
