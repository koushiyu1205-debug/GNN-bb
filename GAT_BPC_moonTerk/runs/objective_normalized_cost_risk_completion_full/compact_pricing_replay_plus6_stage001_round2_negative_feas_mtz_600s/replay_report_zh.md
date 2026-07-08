# Compact Pricing Replay

## Source

- instance: `lunar_ice_sp50_030_001_seed929001`
- selected history round: `2`
- source pricing state: `INCOMPLETE_LIMIT`
- source best RC: `1.179812979`
- source dual bound: `-5.418735362`

## Replay Config

- time limit: `600.0`
- negative feasibility search: `True`
- MTZ connectivity: `True`
- flow connectivity: `False`

## Result

- status: `COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED`
- exact status: `NOT_SOLVED`
- pricing state: `FOUND_NEGATIVE`
- best reduced cost: `-0.638210961`
- dual bound: `-1.144456096`
- gap: `0.793225451`
- negative found: `True`
- can certify no-negative: `False`
- variable count: `70231`
- constraint count: `137490`
- wall time: `552.422922`

该 replay 只重放 compact pricing final-judge 子问题；只有 exact pricing optimal/no-negative 时才可作为 BPC final judge 证书的一部分。
