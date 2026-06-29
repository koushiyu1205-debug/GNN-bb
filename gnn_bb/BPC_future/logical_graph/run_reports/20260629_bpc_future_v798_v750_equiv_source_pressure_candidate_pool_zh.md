# Journey Pressure Candidate Pool

Date: 2026-06-29

## Boundary

This artifact is diagnostic only. It scans existing branch-candidate logs and writes a replay queue; it does not run BPC/pricing/RMP and does not create official lower bounds, certificates, pruning rules, or fathoming decisions.

## Machine Fields

```text
output_dir = BPC_future/results/journey_pressure_candidate_pool_v798_v750_equiv_source_seed61308_seed61744_360
candidate_pool_path = BPC_future/results/journey_pressure_candidate_pool_v798_v750_equiv_source_seed61308_seed61744_360/candidate_pool.jsonl
replay_queue_path = BPC_future/results/journey_pressure_candidate_pool_v798_v750_equiv_source_seed61308_seed61744_360/replay_queue.jsonl
source_event_count = 0
candidate_row_count = 0
queue_row_count = 0
coverage_key_count = 73
coverage_status_counts = {}
candidate_depth_counts = {}
queue_depth_counts = {}
low_pressure_skip_count = 0
duplicate_candidate_count = 0
skipped_missing_instance_event_count = 0
depth_filter_skip_count = 0
source_event_time_filter_skip_count = 0
runs_bpc_or_pricing = false
official_bound_effect = false
certificate_effect = false
```

## Recommended Runbook Command

```bash
python BPC_future/scripts/build_journey_branch_candidate_replay_runbook.py BPC_future/results/20260629_v798_v750_equiv_source_seed61308_seed61744_360/logs --focus-candidate-input BPC_future/results/journey_pressure_candidate_pool_v798_v750_equiv_source_seed61308_seed61744_360/replay_queue.jsonl --candidate-source both --candidate-selection layered --paired-probe
```

## Top Queue Rows

