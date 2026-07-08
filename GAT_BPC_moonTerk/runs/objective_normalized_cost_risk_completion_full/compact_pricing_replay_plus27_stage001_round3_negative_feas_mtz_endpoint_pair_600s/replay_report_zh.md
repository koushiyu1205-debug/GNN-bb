# Compact Pricing Replay

## Source

- instance: `lunar_ice_sp50_030_001_seed929001`
- selected history round: `3`
- source pricing state: `INCOMPLETE_LIMIT`
- source best RC: `0.136422772`
- source dual bound: `-0.632214454`

## Replay Config

- time limit: `600.0`
- negative feasibility search: `True`
- MTZ connectivity: `True`
- flow connectivity: `False`
- MTZ endpoint order cuts: `True`
- pair adjacency cuts: `True`

## Result

- status: `COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED`
- exact status: `NOT_SOLVED`
- pricing state: `FOUND_NEGATIVE`
- best reduced cost: `-0.078614681`
- dual bound: `-0.296753536`
- gap: `2.774777309`
- negative found: `True`
- can certify no-negative: `False`
- MTZ endpoint order cut count: `2898`
- pair adjacency cut count: `8043`
- variable count: `24109`
- constraint count: `57087`
- wall time: `549.51315`

该 replay 只重放 compact pricing final-judge 子问题；只有 exact pricing optimal/no-negative 时才可作为 BPC final judge 证书的一部分。
