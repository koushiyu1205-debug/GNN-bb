# Frozen 5/10 Mainline Baseline - 2026-06-08

This file records the current exact-safe 5-task and 10-task mainline baseline
before 20-task proof-budget work.  The lock is intentionally narrow: 20-task
configs may move, but accidental changes to the 5/10 configs or the learning
checkpoint should fail tests.

## Locked Artifacts

| artifact | sha256 |
| --- | --- |
| `BPC_future/configs/moon_trek_5_journey.yaml` | `a2e351c7b89b4d37caff49474e5d9d281396de2edcd4c2a9e64444e0bf4435ce` |
| `BPC_future/configs/moon_trek_10_journey.yaml` | `f8f896ad9502b36480d46d5b0484171ff6ca64c75ac2057d8750eee5a95b7313` |
| `BPC_future/data/learning_dual/hardtail_20260604/hierarchical_option_gat_hardtail.pt` | `ef7e8a4acdb9d2d6f60a6bd6038ed75d3e89ac72408acd237e5c1054fefcf88d` |

## Validation Snapshot

| run | source CSV | status summary | time summary |
| --- | --- | --- | --- |
| all 5-task instances | `BPC_future/results/full_tasks05_20260608.csv` | 20/20 `OPTIMAL` | total `18.915s`, max `2.665s` |
| all 10-task root-tail-zero instances | `BPC_future/results/all_tasks10_root_tail_zero_gate_20260608.csv` | 20/20 `OPTIMAL` | total `1227.015s`, max `180.381s`, `>200s=0` |

## Exactness Boundary

The learning checkpoint remains an early/mid pricing aid only.  Official
certificates must still come from the true-dual direct-label final judge, with
`CERTIFIED_NO_NEGATIVE`/`direct_label_no_negative_journey` semantics.
