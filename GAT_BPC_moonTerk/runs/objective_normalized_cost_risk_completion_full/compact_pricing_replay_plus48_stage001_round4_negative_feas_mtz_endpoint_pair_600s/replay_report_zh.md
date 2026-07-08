# Compact Pricing Replay

## Source

- instance: `lunar_ice_sp50_030_001_seed929001`
- selected history round: `4`
- source pricing state: `INCOMPLETE_LIMIT`
- source best RC: `None`
- source dual bound: `None`

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
- best reduced cost: `-0.024593926`
- dual bound: `-0.135671544`
- gap: `4.516429332`
- negative found: `True`
- can certify no-negative: `False`
- MTZ endpoint order cut count: `2898`
- pair adjacency cut count: `8043`
- variable count: `24109`
- constraint count: `57087`
- wall time: `549.563264`

该 replay 只重放 compact pricing final-judge 子问题；只有 exact pricing optimal/no-negative 时才可作为 BPC final judge 证书的一部分。
