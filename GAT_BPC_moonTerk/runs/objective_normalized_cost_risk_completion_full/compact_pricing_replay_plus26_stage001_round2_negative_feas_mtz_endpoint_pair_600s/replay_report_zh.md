# Compact Pricing Replay

## Source

- instance: `lunar_ice_sp50_030_001_seed929001`
- selected history round: `2`
- source pricing state: `INCOMPLETE_LIMIT`
- source best RC: `0.025765878`
- source dual bound: `-0.720962577`

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
- best reduced cost: `-0.137198437`
- dual bound: `-0.36743289`
- gap: `1.6781146`
- negative found: `True`
- can certify no-negative: `False`
- MTZ endpoint order cut count: `2898`
- pair adjacency cut count: `8043`
- variable count: `24109`
- constraint count: `57087`
- wall time: `543.478191`

该 replay 只重放 compact pricing final-judge 子问题；只有 exact pricing optimal/no-negative 时才可作为 BPC final judge 证书的一部分。
