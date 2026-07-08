# Compact Pricing Replay

## Source

- instance: `lunar_ice_sp50_030_001_seed929001`
- selected history round: `2`
- source pricing state: `INCOMPLETE_LIMIT`
- source best RC: `None`
- source dual bound: `None`

## Replay Config

- time limit: `600.0`
- negative feasibility search: `False`
- MTZ connectivity: `True`
- flow connectivity: `False`

## Result

- status: `COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED`
- exact status: `NOT_SOLVED`
- pricing state: `FOUND_NEGATIVE`
- best reduced cost: `-0.409595596`
- dual bound: `-0.788716322`
- gap: `0.925598476`
- negative found: `True`
- can certify no-negative: `False`
- variable count: `70231`
- constraint count: `137489`
- wall time: `545.246581`

该 replay 只重放 compact pricing final-judge 子问题；只有 exact pricing optimal/no-negative 时才可作为 BPC final judge 证书的一部分。
