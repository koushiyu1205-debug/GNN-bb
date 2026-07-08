# Compact Pricing Replay

## Source

- instance: `lunar_ice_sp50_030_001_seed929001`
- selected history round: `3`
- source pricing state: `INCOMPLETE_LIMIT`
- source best RC: `None`
- source dual bound: `None`

## Replay Config

- time limit: `600.0`
- negative feasibility search: `False`
- MTZ connectivity: `True`
- flow connectivity: `False`

## Result

- status: `COMPACT_HIGHS_PRICING_OPTIMAL`
- exact status: `EXACT_PRICING_OPTIMAL`
- pricing state: `FOUND_NEGATIVE`
- best reduced cost: `-0.539795608`
- dual bound: `-0.539795536`
- gap: `0.0`
- negative found: `True`
- can certify no-negative: `False`
- variable count: `70231`
- constraint count: `137489`
- wall time: `290.615426`

该 replay 只重放 compact pricing final-judge 子问题；只有 exact pricing optimal/no-negative 时才可作为 BPC final judge 证书的一部分。
