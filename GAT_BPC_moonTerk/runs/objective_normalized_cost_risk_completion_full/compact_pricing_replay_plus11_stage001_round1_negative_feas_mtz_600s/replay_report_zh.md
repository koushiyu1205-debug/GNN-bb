# Compact Pricing Replay

## Source

- instance: `lunar_ice_sp50_030_001_seed929001`
- selected history round: `1`
- source pricing state: `INCOMPLETE_LIMIT`
- source best RC: `1.837737715`
- source dual bound: `-8.076735465`

## Replay Config

- time limit: `600.0`
- negative feasibility search: `True`
- MTZ connectivity: `True`
- flow connectivity: `False`

## Result

- status: `COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED`
- exact status: `NOT_SOLVED`
- pricing state: `INCOMPLETE_LIMIT`
- best reduced cost: `None`
- dual bound: `-9.515639864`
- gap: `None`
- negative found: `False`
- can certify no-negative: `False`
- variable count: `70231`
- constraint count: `137490`
- wall time: `550.943537`

该 replay 只重放 compact pricing final-judge 子问题；只有 exact pricing optimal/no-negative 时才可作为 BPC final judge 证书的一部分。
