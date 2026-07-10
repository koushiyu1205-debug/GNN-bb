# Route-template Negative Probe

## Boundary

- This is an exact-safe negative-column discovery probe.
- It does not certify no-negative and never upgrades BPC status.
- Returned negative columns are manually reduced-cost audited under the current true dual.

## Result

- instance: `lunar_ice_sp50_030_001_seed929001`
- status: `INCREMENTAL_DIRECT_LABEL_NEGATIVE_FOUND`
- wall time: `0.044443` s
- best reduced cost: `-0.00788215`
- negative columns: `1`
- active seeds: `120`
- candidate rounds: `1`
- sortie attempts: `3880`
- feasible route templates: `1551`
- pareto labels: `469`

## Compact Reference

- source: `final_judge`
- wall time: `2.053043` s
- best reduced cost: `None`
- pricing state: `INCOMPLETE_LIMIT`

## Speed

- saved wall time: `2.0086` s
- speedup factor: `46.194969x`

## Negative Columns

- rc `-0.00788215` | tasks `7` | sorties `2` | ice_site_006, ice_site_011, ice_site_020, ice_site_021, ice_site_023, ice_site_024, ice_site_026

## Certificate Boundary

Negative columns are true-dual audited and exact-safe to add. This probe never certifies no-negative because selected task sets are not full-space coverage.
