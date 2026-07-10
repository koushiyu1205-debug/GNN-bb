# Route-template Negative Probe

## Boundary

- This is an exact-safe negative-column discovery probe.
- It does not certify no-negative and never upgrades BPC status.
- Returned negative columns are manually reduced-cost audited under the current true dual.

## Result

- instance: `lunar_ice_sp50_030_001_seed929001`
- status: `INCREMENTAL_DIRECT_LABEL_NEGATIVE_FOUND`
- wall time: `0.456755` s
- best reduced cost: `-0.00788215`
- negative columns: `1`
- active seeds: `120`
- candidate rounds: `13`
- sortie attempts: `40106`
- feasible route templates: `19992`
- pareto labels: `3870`

## Compact Reference

- source: `result`
- wall time: `356.857076` s
- best reduced cost: `-0.0080034`
- pricing state: `FOUND_NEGATIVE`

## Speed

- saved wall time: `356.400321` s
- speedup factor: `781.287728x`

## Negative Columns

- rc `-0.00788215` | tasks `7` | sorties `2` | ice_site_006, ice_site_011, ice_site_020, ice_site_021, ice_site_023, ice_site_024, ice_site_026

## Certificate Boundary

Negative columns are true-dual audited and exact-safe to add. This probe never certifies no-negative because selected task sets are not full-space coverage.
