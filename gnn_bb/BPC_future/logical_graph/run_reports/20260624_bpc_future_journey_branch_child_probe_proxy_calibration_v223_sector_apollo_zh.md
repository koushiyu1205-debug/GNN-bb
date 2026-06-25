# Journey Branch Child-Probe Proxy Calibration

Date: 2026-06-24

## Machine Fields

```text
raw_proxy_row_count = 4
raw_delta_row_count = 6
matched_pair_count = 4
unmatched_proxy_count = 0
duplicate_delta_key_count = 0
context_count = 1
top_pair_match_count = 0
top_pair_mismatch_count = 1
pairwise_comparison_count = 6
discordant_pair_count = 2
discordant_pair_rate = 0.333333333
label_type_counts = {'strong_positive': 4}
sampling_navigation_ready = True
ranking_training_ready = False
production_ready = False
certificate_effect = False
official_bound_effect = False
```

## Contexts

- node=0 depth=0 matched=4 top_proxy=[3, 6] top_full=[6, 16] top_pair_match=False

## Boundary

This calibration is diagnostic-only. A child-probe proxy mismatch against full replay means the proxy should guide sampling, not production branch-score training.
