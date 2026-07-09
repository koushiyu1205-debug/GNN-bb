# Compact Pricing Replay

## Source

- instance: `lunar_ice_sp50_030_001_seed929001`
- selected history round: `3`
- source pricing state: `INCOMPLETE_LIMIT`
- source best RC: `None`
- source dual bound: `None`

## Replay Config

- time limit: `900.0`
- negative feasibility search: `False`
- MTZ connectivity: `False`
- flow connectivity: `False`
- MTZ endpoint order cuts: `True`
- pair adjacency cuts: `True`
- latest-service-start slot bound: `True`
- time-window arc pruning: `True`

## Result

- status: `COMPACT_HIGHS_PRICING_OPTIMAL`
- exact status: `EXACT_PRICING_OPTIMAL`
- pricing state: `FOUND_NEGATIVE`
- best reduced cost: `-0.0080034`
- dual bound: `-0.008003885`
- gap: `0.0`
- negative found: `True`
- can certify no-negative: `False`
- MTZ endpoint order cut count: `0`
- pair adjacency cut count: `8043`
- latest-service-start slot bound enabled: `True`
- sortie slot bound source: `latest_service_start_min_active_sortie_duration_bound`
- time-window arc pruning enabled: `True`
- time-window impossible arc options: `1193`
- variable count: `23479`
- constraint count: `33692`
- wall time: `356.857076`

该 replay 只重放 compact pricing final-judge 子问题；只有 exact pricing optimal/no-negative 时才可作为 BPC final judge 证书的一部分。
