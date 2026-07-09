# Compact Pricing Replay

## Source

- instance: `lunar_ice_sp50_030_001_seed929001`
- selected history round: `1`
- source pricing state: `INCOMPLETE_LIMIT`
- source best RC: `-1e-06`
- source dual bound: `-1.382e-06`

## Replay Config

- time limit: `300.0`
- negative feasibility search: `True`
- MTZ connectivity: `True`
- flow connectivity: `False`
- MTZ endpoint order cuts: `True`
- pair adjacency cuts: `True`
- latest-service-start slot bound: `True`
- time-window arc pruning: `True`
- service-start depot-travel LB: `True`
- task-to-depot return-travel LB: `True`
- pair route-duration LB: `True`
- sortie slot-position bounds: `True`
- demand cover cut: `False`
- single-task energy LB: `False`
- single-task shadow LB: `False`
- pair energy LB: `False`
- pair energy infeasible cut: `True`
- pair shadow infeasible cut: `False`
- triple shadow infeasible cut: `False`
- triple energy infeasible cut: `False`
- triple time-window infeasible cut: `True`
- quad time-window infeasible cut: `False`

## Result

- status: `COMPACT_HIGHS_PRICING_OPTIMAL`
- exact status: `EXACT_PRICING_OPTIMAL`
- pricing state: `FOUND_NEGATIVE`
- best reduced cost: `-1e-06`
- dual bound: `-1.382e-06`
- gap: `0.0`
- negative found: `True`
- can certify no-negative: `False`
- MTZ endpoint order cut count: `2898`
- pair adjacency cut count: `8043`
- latest-service-start slot bound enabled: `True`
- sortie slot bound source: `latest_service_start_min_active_sortie_duration_bound`
- time-window arc pruning enabled: `True`
- time-window impossible arc options: `1193`
- service-start depot-travel LB enabled: `True`
- service-start depot-travel LB rows: `630`
- task-to-depot return-travel LB enabled: `True`
- task-to-depot return-travel LB rows: `630`
- pair route-duration LB enabled: `True`
- pair route-duration LB rows: `9135`
- sortie slot-position bounds enabled: `True`
- sortie slot-position bounds rows: `62`
- demand cover cut enabled: `False`
- demand cover cut rows: `0`
- single-task energy LB enabled: `False`
- single-task energy LB rows: `0`
- single-task shadow LB enabled: `False`
- single-task shadow LB rows: `0`
- pair energy LB enabled: `False`
- pair energy LB rows: `0`
- pair energy infeasible cut enabled: `True`
- pair energy infeasible cut rows: `777`
- pair shadow infeasible cut enabled: `False`
- pair shadow infeasible cut rows: `0`
- triple shadow infeasible cut enabled: `False`
- triple shadow infeasible cut rows: `0`
- triple energy infeasible cut enabled: `False`
- triple energy infeasible cut rows: `0`
- triple time-window infeasible cut enabled: `True`
- triple time-window infeasible cut rows: `27909`
- quad time-window infeasible cut enabled: `False`
- quad time-window infeasible cut rows: `0`
- variable count: `24109`
- constraint count: `96230`
- wall time: `212.531174`

该 replay 只重放 compact pricing final-judge 子问题；只有 exact pricing optimal/no-negative 时才可作为 BPC final judge 证书的一部分。
