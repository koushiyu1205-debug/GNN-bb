# Compact Pricing Replay

## Source

- instance: `lunar_ice_sp50_030_001_seed929001`
- selected history round: `3`
- source pricing state: `INCOMPLETE_LIMIT`
- source best RC: `None`
- source dual bound: `None`

## Replay Config

- time limit: `120.0`
- negative feasibility search: `True`
- MTZ connectivity: `False`
- flow connectivity: `False`

## Result

- status: `COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED`
- exact status: `NOT_SOLVED`
- pricing state: `FOUND_NEGATIVE`
- best reduced cost: `-0.524984285`
- dual bound: `-0.886162522`
- gap: `0.687977794`
- negative found: `True`
- can certify no-negative: `False`
- variable count: `69331`
- constraint count: `72420`
- wall time: `109.115125`

该 replay 只重放 compact pricing final-judge 子问题；只有 exact pricing optimal/no-negative 时才可作为 BPC final judge 证书的一部分。
