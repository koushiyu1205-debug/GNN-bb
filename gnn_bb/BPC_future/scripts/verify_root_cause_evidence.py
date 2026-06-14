#!/usr/bin/env python3
"""Verify the current BPC_future root-cause evidence ledger from local artifacts.

This script is intentionally read-only with respect to solver state: it only
reads existing reports and summary files, then writes a compact evidence ledger.
It does not run BPC, pricing, Pulse, RMP, or any benchmark.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/root_cause_evidence_ledger_20260613")
SMALL_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260613_bpc_future_root_cause_small_scale_overhead_guard_audit_zh.md"
)
PHASE7O_SUMMARY = Path(
    "BPC_future/results/sharded_pulse_phase7o_hard_tail_worker_roi_ab_20260612/summary.csv"
)
PHASE8Q_SUMMARY = Path(
    "BPC_future/results/sharded_pulse_phase8q_passed_source_roi_validation_smoke_20260613/summary.csv"
)
CANDIDATE_SUMMARY = Path(
    "BPC_future/results/root_cause_returned_batch_trajectory_dataset_20260613/summary.json"
)
CANDIDATE_MODEL_SUMMARY = Path(
    "BPC_future/results/root_cause_candidate_selector_models_20260613/summary.json"
)
SELECTOR_FAILURE_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_failure_anatomy_20260613/summary.json"
)
HINDSIGHT_ORACLE_GAP_SUMMARY = Path(
    "BPC_future/results/root_cause_hindsight_oracle_gap_20260613/summary.json"
)
CANDIDATE_LABEL_GRANULARITY_SUMMARY = Path(
    "BPC_future/results/root_cause_candidate_label_granularity_20260613/summary.json"
)
BATCH_LEVEL_SELECTOR_SUMMARY = Path(
    "BPC_future/results/root_cause_batch_level_selector_20260613/summary.json"
)
TRAJECTORY_SIGNAL_LADDER_SUMMARY = Path(
    "BPC_future/results/root_cause_trajectory_signal_ladder_20260613/summary.json"
)
BATCH_GATE_STABILITY_SUMMARY = Path(
    "BPC_future/results/root_cause_batch_gate_stability_20260613/summary.json"
)
CONTEXT_STRATIFICATION_SUMMARY = Path(
    "BPC_future/results/root_cause_context_stratification_20260613/summary.json"
)
CONTEXT_ONLY_BASELINE_SUMMARY = Path(
    "BPC_future/results/root_cause_context_only_baseline_20260613/summary.json"
)
MATCHED_CONTEXT_AUDIT_SUMMARY = Path(
    "BPC_future/results/root_cause_matched_context_audit_20260613/summary.json"
)
MATCHED_CONTEXT_PAIRWISE_SUMMARY = Path(
    "BPC_future/results/root_cause_matched_context_pairwise_contrast_20260613/summary.json"
)
EXACT_CONTEXT_LABEL_CONFLICTS_SUMMARY = Path(
    "BPC_future/results/root_cause_exact_context_label_conflicts_20260613/summary.json"
)
COUNTERFACTUAL_REPLAY_COVERAGE_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_replay_coverage_20260613/summary.json"
)
COUNTERFACTUAL_REPLAY_CANDIDATES_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_replay_candidates_20260613/summary.json"
)
COUNTERFACTUAL_REPLAY_READINESS_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_replay_readiness_20260613/summary.json"
)
COUNTERFACTUAL_REPLAY_MATERIALIZATION_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_replay_materialization_20260613/"
    "summary.json"
)
COUNTERFACTUAL_REPLAY_CAPTURE_SMOKE_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_replay_capture_smoke_20260613/"
    "audit/summary.json"
)
COUNTERFACTUAL_REPLAY_MANIFEST_SMOKE_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_replay_capture_smoke_20260613/"
    "replay_manifest/summary.json"
)
COUNTERFACTUAL_REPLAY_FEASIBLE_SMOKE_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_replay_feasible_smoke_20260613/"
    "replay_result/summary.json"
)
COUNTERFACTUAL_REPLAY_GAP_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_replay_gap_20260613/"
    "summary.json"
)
COUNTERFACTUAL_REPLAY_REAL_CAPTURE_AUDIT_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_replay_real_capture_mt20_apollo_20260613/"
    "audit_v2/summary.json"
)
COUNTERFACTUAL_REPLAY_REAL_CAPTURE_MANIFEST_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_replay_real_capture_mt20_apollo_20260613/"
    "replay_manifest_v2/summary.json"
)
COUNTERFACTUAL_REPLAY_REAL_CAPTURE_RESULT_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_replay_real_capture_mt20_apollo_20260613/"
    "replay_result_v2/summary.json"
)
COUNTERFACTUAL_REPLAY_IMPACT_REAL_CAPTURE_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/"
    "real_capture_mt20_apollo/summary.json"
)
COUNTERFACTUAL_REPLAY_IMPACT_DUPLICATE_NOOP_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/"
    "duplicate_noop_smoke/summary.json"
)
COUNTERFACTUAL_REPLAY_IMPACT_COMBINED_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/"
    "combined/summary.json"
)
COUNTERFACTUAL_REPLAY_PAYLOAD_QUALITY_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260613_bpc_future_root_cause_counterfactual_replay_payload_quality_audit_zh.md"
)
COUNTERFACTUAL_REPLAY_PAYLOAD_QUALITY_AUDIT_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_replay_real_capture_mt20_apollo_20260613/"
    "audit_all_logs/summary.json"
)
COUNTERFACTUAL_REPLAY_PAYLOAD_QUALITY_MANIFEST_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_replay_real_capture_mt20_apollo_20260613/"
    "replay_manifest_all_logs/summary.json"
)
COUNTERFACTUAL_REPLAY_PAYLOAD_QUALITY_REPLAY_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_replay_real_capture_mt20_apollo_20260613/"
    "replay_result_all_logs/summary.json"
)
COUNTERFACTUAL_REPLAY_PAYLOAD_QUALITY_IMPACT_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/"
    "real_capture_mt20_apollo_all_logs/summary.json"
)
COUNTERFACTUAL_REPLAY_CAPTURE_EXPANSION_MT20_TRANQ_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_replay_real_capture_mt20_tranq_20260613/"
    "summary.json"
)
COUNTERFACTUAL_REPLAY_CAPTURE_EXPANSION_MT20_TRANQ_AUDIT_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_replay_real_capture_mt20_tranq_20260613/"
    "audit/summary.json"
)
COUNTERFACTUAL_REPLAY_CAPTURE_EXPANSION_TRANQ20_01_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_replay_real_capture_tranq20_01_20260613/"
    "summary.json"
)
COUNTERFACTUAL_REPLAY_CAPTURE_EXPANSION_TRANQ20_01_AUDIT_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_replay_real_capture_tranq20_01_20260613/"
    "audit/summary.json"
)
COUNTERFACTUAL_REPLAY_GLOBAL_CAPTURE_SCAN_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260613_bpc_future_root_cause_counterfactual_replay_global_capture_scan_zh.md"
)
COUNTERFACTUAL_REPLAY_GLOBAL_CAPTURE_SCAN_AUDIT_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_replay_global_capture_scan_20260613/"
    "audit/summary.json"
)
COUNTERFACTUAL_REPLAY_GLOBAL_CAPTURE_SCAN_MANIFEST = Path(
    "BPC_future/results/root_cause_counterfactual_replay_global_capture_scan_20260613/"
    "replay_manifest/replay_cases.json"
)
COUNTERFACTUAL_REPLAY_GLOBAL_CAPTURE_SCAN_MANIFEST_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_replay_global_capture_scan_20260613/"
    "replay_manifest/summary.json"
)
COUNTERFACTUAL_REPLAY_GLOBAL_CAPTURE_SCAN_REPLAY_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_replay_global_capture_scan_20260613/"
    "replay_result/summary.json"
)
COUNTERFACTUAL_REPLAY_GLOBAL_CAPTURE_SCAN_IMPACT_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_replay_global_capture_scan_20260613/"
    "impact/summary.json"
)
COUNTERFACTUAL_REPLAY_CANDIDATE_TO_CAPTURE_GAP_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260613_bpc_future_root_cause_replay_candidate_to_capture_gap_zh.md"
)
COUNTERFACTUAL_CAPTURE_TARGETS_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260613_bpc_future_root_cause_counterfactual_capture_targets_zh.md"
)
COUNTERFACTUAL_CAPTURE_TARGETS_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_capture_targets_20260613/"
    "summary.json"
)
COUNTERFACTUAL_CAPTURE_TARGET_COVERAGE_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260613_bpc_future_root_cause_counterfactual_capture_target_coverage_zh.md"
)
COUNTERFACTUAL_CAPTURE_TARGET_COVERAGE_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_capture_target_coverage_20260613/"
    "summary.json"
)
COUNTERFACTUAL_TARGET_TRANQ20_REPLAY_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260613_bpc_future_root_cause_counterfactual_target_tranq20_replay_zh.md"
)
COUNTERFACTUAL_TARGET_TRANQ20_CAPTURE_AUDIT_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_tranq20_20260613/"
    "audit/summary.json"
)
COUNTERFACTUAL_TARGET_TRANQ20_MANIFEST_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_tranq20_20260613/"
    "replay_manifest/summary.json"
)
COUNTERFACTUAL_TARGET_TRANQ20_REPLAY_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_tranq20_20260613/"
    "replay_result/summary.json"
)
COUNTERFACTUAL_TARGET_TRANQ20_IMPACT_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_tranq20_20260613/"
    "impact/summary.json"
)
COUNTERFACTUAL_TARGET_001_002_REPLAY_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260613_bpc_future_root_cause_counterfactual_target_001_002_replay_zh.md"
)
COUNTERFACTUAL_TARGET_001_002_CAPTURE_AUDIT_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/"
    "audit/summary.json"
)
COUNTERFACTUAL_TARGET_001_002_MANIFEST_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/"
    "replay_manifest/summary.json"
)
COUNTERFACTUAL_TARGET_001_002_REPLAY_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/"
    "replay_result/summary.json"
)
COUNTERFACTUAL_TARGET_001_002_IMPACT_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/"
    "impact/summary.json"
)
TARGET002_REPRODUCTION_GAP_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260613_bpc_future_root_cause_target002_reproduction_gap_zh.md"
)
TARGET002_NO_CAPTURE_MIRROR_SUMMARY = Path(
    "BPC_future/results/root_cause_target002_current_code_no_capture_mirror_20260613/"
    "summary.csv"
)
TARGET002_PT03_RECOVERY_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260613_bpc_future_root_cause_target002_pt03_recovery_and_selector_shift_zh.md"
)
TARGET002_NO_CAPTURE_MIRROR_PT03_SUMMARY = Path(
    "BPC_future/results/root_cause_target002_current_code_no_capture_mirror_pt03_r3_20260613/"
    "summary.csv"
)
TARGET002_PT03_CAPTURE_AUDIT_SUMMARY = Path(
    "BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/"
    "audit/summary.json"
)
TARGET002_PT03_MANIFEST_SUMMARY = Path(
    "BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/"
    "replay_manifest/summary.json"
)
TARGET002_PT03_REPLAY_SUMMARY = Path(
    "BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/"
    "replay_result/summary.json"
)
TARGET002_PT03_IMPACT_SUMMARY = Path(
    "BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/"
    "impact/summary.json"
)
COUNTERFACTUAL_CAPTURE_TARGET_COVERAGE_AFTER_TARGET002_PT03_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_capture_target_coverage_after_target002_pt03_20260613/"
    "summary.json"
)
COUNTERFACTUAL_REPLAY_SELECTOR_GATE_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_replay_selector_gate_20260613/"
    "summary.json"
)
COUNTERFACTUAL_REPLAY_PAIR_SELECTOR_GATE_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_replay_pair_selector_gate_20260613/"
    "summary.json"
)
COUNTERFACTUAL_REPLAY_MODEL_SELECTOR_GATE_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_replay_model_selector_gate_20260613/"
    "summary.json"
)
COUNTERFACTUAL_REPLAY_SELECTOR_GATE_WITH_TARGET002_PT03_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_replay_selector_gate_with_target002_pt03_20260613/"
    "summary.json"
)
COUNTERFACTUAL_REPLAY_PAIR_SELECTOR_GATE_WITH_TARGET002_PT03_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_replay_pair_selector_gate_with_target002_pt03_20260613/"
    "summary.json"
)
COUNTERFACTUAL_REPLAY_MODEL_SELECTOR_GATE_WITH_TARGET002_PT03_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_replay_model_selector_gate_with_target002_pt03_20260613/"
    "summary.json"
)
REPLAY_CALIBRATED_SELECTOR_CANDIDATE_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260613_bpc_future_root_cause_replay_calibrated_selector_candidate_zh.md"
)
REPLAY_CALIBRATED_SELECTOR_CANDIDATE_SUMMARY = Path(
    "BPC_future/results/root_cause_replay_calibrated_selector_candidate_20260613/"
    "summary.json"
)
CALIBRATED_SELECTOR_AB_PROFILE_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260613_bpc_future_root_cause_calibrated_selector_ab_profile_smoke_zh.md"
)
CALIBRATED_SELECTOR_GATE_SMOKE_CSV = Path(
    "BPC_future/results/root_cause_calibrated_selector_gate_smoke_20260613/"
    "summary.csv"
)
CALIBRATED_SELECTOR_MT20_APOLLO_SMOKE_CSV = Path(
    "BPC_future/results/root_cause_calibrated_selector_20_smoke_20260613/"
    "summary.csv"
)
CALIBRATED_SELECTOR_TRANQ20_SMOKE_CSV = Path(
    "BPC_future/results/root_cause_calibrated_selector_tranq20_smoke_20260613/"
    "summary.csv"
)
CALIBRATED_SELECTOR_MT20_TRANQ_SMOKE_CSV = Path(
    "BPC_future/results/root_cause_calibrated_selector_mt20_tranq_smoke_20260613/"
    "summary.csv"
)
CALIBRATED_SELECTOR_HARDTAIL_WORKER_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260613_bpc_future_root_cause_calibrated_selector_hardtail_worker_smoke_zh.md"
)
CALIBRATED_SELECTOR_HARDTAIL_WORKER_SMOKE_CSV = Path(
    "BPC_future/results/root_cause_calibrated_selector_hardtail_worker_smoke_20260613/"
    "summary.csv"
)
CALIBRATED_SELECTOR_HARDTAIL_GATE_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260613_bpc_future_root_cause_calibrated_selector_hardtail_gate_smoke_zh.md"
)
CALIBRATED_SELECTOR_HARDTAIL_GATE_SMOKE_CSV = Path(
    "BPC_future/results/root_cause_calibrated_selector_hardtail_gate_smoke_20260613/"
    "summary.csv"
)
CALIBRATED_SELECTOR_HARDTAIL_REPEAT_GATE_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260613_bpc_future_root_cause_calibrated_selector_hardtail_repeat_gate_zh.md"
)
CALIBRATED_SELECTOR_HARDTAIL_REPEAT_GATE_CSV = Path(
    "BPC_future/results/root_cause_calibrated_selector_hardtail_repeat_gate_20260613/"
    "summary.csv"
)
CALIBRATED_SELECTOR_SELECTED20_REPEAT_AB_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260613_bpc_future_root_cause_calibrated_selector_selected20_repeat_ab_zh.md"
)
CALIBRATED_SELECTOR_SELECTED20_REPEAT_AB_CSV = Path(
    "BPC_future/results/root_cause_calibrated_selector_selected20_repeat_ab_20260613/"
    "summary.csv"
)
COUNTERFACTUAL_REPLAY_DATASET_STRUCTURE_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_replay_dataset_structure_20260613/"
    "summary.json"
)
COUNTERFACTUAL_REPLAY_DATASET_STRUCTURE_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260613_bpc_future_root_cause_counterfactual_replay_dataset_structure_zh.md"
)
COUNTERFACTUAL_CAPTURE_PRIORITY_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_capture_priority_20260613/"
    "summary.json"
)
COUNTERFACTUAL_CAPTURE_PRIORITY_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260613_bpc_future_root_cause_counterfactual_capture_priority_zh.md"
)
FINAL_REPORT = Path(
    "BPC_future/logical_graph/run_reports/20260613_bpc_future_root_cause_final_synthesis_zh.md"
)
REQUIREMENT_AUDIT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260613_bpc_future_root_cause_requirement_audit_zh.md"
)
OPTIMIZATION_DIRECTION_READINESS_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260613_bpc_future_root_cause_optimization_direction_readiness_audit_zh.md"
)
ROOT_CAUSE_DIAGNOSIS_REPORT = Path(
    "BPC_future/docs/bpc_future_root_cause_diagnosis_zh.md"
)
GOAL_COMPLETION_BLOCKERS_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_goal_completion_blockers_zh.md"
)
WHY_MANY_ATTEMPTS_FAILED_SUMMARY = Path(
    "BPC_future/results/root_cause_why_many_attempts_failed_20260614/"
    "summary.json"
)
WHY_MANY_ATTEMPTS_FAILED_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_why_many_attempts_failed_zh.md"
)
ROOT_CAUSE_CAUSAL_CHAIN_AUDIT_SUMMARY = Path(
    "BPC_future/results/root_cause_causal_chain_audit_20260614/summary.json"
)
ROOT_CAUSE_CAUSAL_CHAIN_AUDIT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_causal_chain_audit_zh.md"
)
ROOT_CAUSE_CURRENT_ANSWER_SUMMARY = Path(
    "BPC_future/results/root_cause_current_answer_20260614/summary.json"
)
ROOT_CAUSE_CURRENT_ANSWER_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_current_answer_zh.md"
)
ROOT_CAUSE_STALE_CLAIMS_SUMMARY = Path(
    "BPC_future/results/root_cause_stale_claims_20260614/summary.json"
)
ROOT_CAUSE_STALE_CLAIMS_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_stale_claims_zh.md"
)
ROOT_CAUSE_MISSING_REQUIREMENT_EVIDENCE_SCAN_SUMMARY = Path(
    "BPC_future/results/root_cause_missing_requirement_evidence_scan_20260614/"
    "summary.json"
)
ROOT_CAUSE_MISSING_REQUIREMENT_EVIDENCE_SCAN_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_missing_requirement_evidence_scan_zh.md"
)
ROOT_CAUSE_NEXT_ACTION_PLAN_SUMMARY = Path(
    "BPC_future/results/root_cause_next_action_plan_20260614/summary.json"
)
ROOT_CAUSE_NEXT_ACTION_PLAN_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_next_action_plan_zh.md"
)
ROOT_CAUSE_DOCUMENT_CONSISTENCY_SUMMARY = Path(
    "BPC_future/results/root_cause_document_consistency_20260614/summary.json"
)
ROOT_CAUSE_DOCUMENT_CONSISTENCY_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_document_consistency_zh.md"
)
ROOT_CAUSE_SELECTOR_COLLECTION_PLAN_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_collection_plan_20260614/summary.json"
)
ROOT_CAUSE_SELECTOR_COLLECTION_PLAN_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_collection_plan_zh.md"
)
ROOT_CAUSE_SELECTOR_COLLECTION_SCHEMA_COVERAGE_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_collection_schema_coverage_20260614/"
    "summary.json"
)
ROOT_CAUSE_SELECTOR_COLLECTION_SCHEMA_COVERAGE_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_collection_schema_coverage_zh.md"
)
ROOT_CAUSE_SELECTOR_HOLDOUT_COLLECTION_MANIFEST_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_holdout_collection_manifest_20260614/"
    "summary.json"
)
ROOT_CAUSE_SELECTOR_HOLDOUT_COLLECTION_MANIFEST_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_holdout_collection_manifest_zh.md"
)
ROOT_CAUSE_SELECTOR_HOLDOUT_COLLECTION_RUNBOOK_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_holdout_collection_runbook_20260614/"
    "summary.json"
)
ROOT_CAUSE_SELECTOR_HOLDOUT_COLLECTION_RUNBOOK_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_holdout_collection_runbook_zh.md"
)
ROOT_CAUSE_SELECTOR_HOLDOUT_COLLECTION_CAPTURE_AUDIT_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_holdout_collection_capture_audit_20260614/"
    "summary.json"
)
ROOT_CAUSE_SELECTOR_HOLDOUT_COLLECTION_CAPTURE_AUDIT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_holdout_collection_capture_audit_zh.md"
)
ROOT_CAUSE_SELECTOR_HOLDOUT_PRIORITY_COLLECTION_CAPTURE_AUDIT_SUMMARY = Path(
    "BPC_future/results/"
    "root_cause_selector_holdout_priority_collection_capture_audit_20260614/"
    "summary.json"
)
ROOT_CAUSE_SELECTOR_HOLDOUT_PRIORITY_COLLECTION_CAPTURE_AUDIT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_holdout_priority_collection_capture_audit_zh.md"
)
ROOT_CAUSE_SELECTOR_HOLDOUT_PRIORITY_CAPTURE_MISS_SUMMARY = Path(
    "BPC_future/results/"
    "root_cause_selector_holdout_priority_capture_miss_20260614/summary.json"
)
ROOT_CAUSE_SELECTOR_HOLDOUT_PRIORITY_CAPTURE_MISS_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_holdout_priority_capture_miss_zh.md"
)
ROOT_CAUSE_SELECTOR_HOLDOUT_BLOCKER_STATUS_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_holdout_blocker_status_20260614/"
    "summary.json"
)
ROOT_CAUSE_SELECTOR_HOLDOUT_BLOCKER_STATUS_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_holdout_blocker_status_zh.md"
)
ROOT_CAUSE_WORKER_NEGATIVE_COLUMN_ROI_BLOCKER_SUMMARY = Path(
    "BPC_future/results/root_cause_worker_negative_column_roi_blocker_20260614/"
    "summary.json"
)
ROOT_CAUSE_WORKER_NEGATIVE_COLUMN_ROI_BLOCKER_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_worker_negative_column_roi_blocker_zh.md"
)
ROOT_CAUSE_SELECTOR_CONTEXT_TRAJECTORY_PROTOCOL_SUMMARY = Path(
    "BPC_future/results/"
    "root_cause_selector_context_trajectory_capture_protocol_20260614/summary.json"
)
ROOT_CAUSE_SELECTOR_CONTEXT_TRAJECTORY_PROTOCOL_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_context_trajectory_capture_protocol_zh.md"
)
ROOT_CAUSE_SELECTOR_HOLDOUT_CONTEXT_WORKLIST_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_holdout_context_worklist_20260614/"
    "summary.json"
)
ROOT_CAUSE_SELECTOR_HOLDOUT_CONTEXT_WORKLIST_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_holdout_context_worklist_zh.md"
)
ROOT_CAUSE_SELECTOR_HOLDOUT_CONTEXT_ACTION_PLAN_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_holdout_context_action_plan_20260614/"
    "summary.json"
)
ROOT_CAUSE_SELECTOR_HOLDOUT_CONTEXT_ACTION_PLAN_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_holdout_context_action_plan_zh.md"
)
ROOT_CAUSE_SELECTOR_HOLDOUT_TARGET002_DRIFT_AUDIT_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_holdout_target002_drift_audit_20260614/"
    "summary.json"
)
ROOT_CAUSE_SELECTOR_HOLDOUT_TARGET002_DRIFT_AUDIT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_holdout_target002_drift_audit_zh.md"
)
ROOT_CAUSE_SELECTOR_HOLDOUT_TARGET002_PROBE_MATRIX_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_holdout_target002_probe_matrix_20260614/"
    "summary.json"
)
ROOT_CAUSE_SELECTOR_HOLDOUT_TARGET002_PROBE_MATRIX_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_holdout_target002_probe_matrix_zh.md"
)
ROOT_CAUSE_SELECTOR_HOLDOUT_TARGET002_TRAJECTORY_BRANCH_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_holdout_target002_trajectory_branch_20260614/"
    "summary.json"
)
ROOT_CAUSE_SELECTOR_HOLDOUT_TARGET002_TRAJECTORY_BRANCH_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_holdout_target002_trajectory_branch_zh.md"
)
ROOT_CAUSE_SELECTOR_HOLDOUT_MISSING_CONTEXT_DIAGNOSIS_SUMMARY = Path(
    "BPC_future/results/"
    "root_cause_selector_holdout_missing_context_diagnosis_20260614/summary.json"
)
ROOT_CAUSE_SELECTOR_HOLDOUT_MISSING_CONTEXT_DIAGNOSIS_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_holdout_missing_context_diagnosis_zh.md"
)
ROOT_CAUSE_SELECTOR_HOLDOUT_TARGET002_COMPONENT_DRIFT_SUMMARY = Path(
    "BPC_future/results/"
    "root_cause_selector_holdout_target002_component_drift_20260614/summary.json"
)
ROOT_CAUSE_SELECTOR_HOLDOUT_TARGET002_COMPONENT_DRIFT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_holdout_target002_component_drift_zh.md"
)
ROOT_CAUSE_SELECTOR_COMPONENT_FEATURE_READINESS_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_component_feature_readiness_20260614/"
    "summary.json"
)
ROOT_CAUSE_SELECTOR_COMPONENT_FEATURE_READINESS_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_component_feature_readiness_zh.md"
)
ROOT_CAUSE_SELECTOR_COMPONENT_CAPTURE_SCHEMA_CONTRACT_SUMMARY = Path(
    "BPC_future/results/"
    "root_cause_selector_component_capture_schema_contract_20260614/summary.json"
)
ROOT_CAUSE_SELECTOR_COMPONENT_CAPTURE_SCHEMA_CONTRACT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_component_capture_schema_contract_zh.md"
)
ROOT_CAUSE_COMPONENT_PAYLOAD_ADDITION_BEFORE_ROWS_SUMMARY = Path(
    "BPC_future/results/root_cause_component_payload_addition_before_rows_20260614/"
    "summary.json"
)
ROOT_CAUSE_COMPONENT_PAYLOAD_ADDITION_BEFORE_ROWS_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_component_payload_addition_before_rows_zh.md"
)
ROOT_CAUSE_COMPONENT_PAYLOAD_SELECTOR_HOLDOUT_EXTENSION_SUMMARY = Path(
    "BPC_future/results/"
    "root_cause_component_payload_selector_holdout_extension_20260614/summary.json"
)
ROOT_CAUSE_COMPONENT_PAYLOAD_SELECTOR_HOLDOUT_EXTENSION_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_component_payload_selector_holdout_extension_zh.md"
)
ROOT_CAUSE_SELECTOR_CONTEXT_SUFFICIENCY_GAP_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_context_sufficiency_gap_20260614/"
    "summary.json"
)
ROOT_CAUSE_SELECTOR_CONTEXT_SUFFICIENCY_GAP_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_context_sufficiency_gap_zh.md"
)
ROOT_CAUSE_SELECTOR_POOL_OVERLAP_FEATURE_PROBE_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_pool_overlap_feature_probe_20260614/"
    "summary.json"
)
ROOT_CAUSE_SELECTOR_POOL_OVERLAP_FEATURE_PROBE_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_pool_overlap_feature_probe_zh.md"
)
ROOT_CAUSE_SELECTOR_CONTEXT_SCHEMA_GAP_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_context_schema_gap_20260614/"
    "summary.json"
)
ROOT_CAUSE_SELECTOR_CONTEXT_SCHEMA_GAP_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_context_schema_gap_zh.md"
)
ROOT_CAUSE_SELECTOR_SNAPSHOT_SAMPLE_COVERAGE_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_snapshot_sample_coverage_20260614/"
    "summary.json"
)
ROOT_CAUSE_SELECTOR_SNAPSHOT_SAMPLE_COVERAGE_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_snapshot_sample_coverage_zh.md"
)
ROOT_CAUSE_SELECTOR_NEXT_FEATURE_GATE_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_next_feature_gate_20260614/"
    "summary.json"
)
ROOT_CAUSE_SELECTOR_NEXT_FEATURE_GATE_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_next_feature_gate_zh.md"
)
OBJECTIVE_COMPLETION_AUDIT_SUMMARY = Path(
    "BPC_future/results/root_cause_objective_completion_audit_20260614/"
    "summary.json"
)
OBJECTIVE_COMPLETION_AUDIT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_objective_completion_audit_zh.md"
)
NEXT_EVIDENCE_PROTOCOL_CATALOG_SUMMARY = Path(
    "BPC_future/results/root_cause_next_evidence_protocol_catalog_20260614/"
    "summary.json"
)
NEXT_EVIDENCE_PROTOCOL_CATALOG_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_next_evidence_protocol_catalog_zh.md"
)
EVIDENCE_BUNDLE_MANIFEST_SUMMARY = Path(
    "BPC_future/results/root_cause_evidence_bundle_manifest_20260614/"
    "summary.json"
)
EVIDENCE_BUNDLE_MANIFEST_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_evidence_bundle_manifest_zh.md"
)
EVIDENCE_BUNDLE_REBUILD_SCRIPT = Path(
    "BPC_future/scripts/rebuild_root_cause_evidence_bundle.py"
)
EVIDENCE_BUNDLE_REBUILD_SUMMARY = Path(
    "BPC_future/results/root_cause_evidence_rebuild_20260614/summary.json"
)
EVIDENCE_BUNDLE_REBUILD_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_evidence_rebuild_zh.md"
)
GOAL_SUMMARY = Path("BPC_future/logical_graph/目标.md")
EXACT_CONTEXT_CAPTURE_STATUS_SUMMARY = Path(
    "BPC_future/results/root_cause_exact_context_capture_status_20260613/"
    "summary.json"
)
EXACT_CONTEXT_CAPTURE_STATUS_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260613_bpc_future_root_cause_exact_context_capture_status_zh.md"
)
SELECTOR_HOLDOUT_STATUS_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_holdout_status_20260613/summary.json"
)
SELECTOR_HOLDOUT_STATUS_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260613_bpc_future_root_cause_selector_holdout_status_zh.md"
)
SELECTOR_ERROR_ANATOMY_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_error_anatomy_20260613/summary.json"
)
SELECTOR_ERROR_ANATOMY_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260613_bpc_future_root_cause_selector_error_anatomy_zh.md"
)
SELECTOR_COUNTEREXAMPLE_CATALOG_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_counterexample_catalog_20260614/"
    "summary.json"
)
SELECTOR_COUNTEREXAMPLE_CATALOG_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_counterexample_catalog_zh.md"
)
PRODUCTION_SELECTOR_BLOCKER_CATALOG_SUMMARY = Path(
    "BPC_future/results/root_cause_production_selector_blocker_catalog_20260614/"
    "summary.json"
)
PRODUCTION_SELECTOR_BLOCKER_CATALOG_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_production_selector_blocker_catalog_zh.md"
)
SELECTOR_FAILURE_MECHANISM_AUDIT_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_failure_mechanism_audit_20260614/"
    "summary.json"
)
SELECTOR_FAILURE_MECHANISM_AUDIT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_failure_mechanism_audit_zh.md"
)
SELECTOR_CONTEXT_FEATURE_GAP_AUDIT_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_context_feature_gap_audit_20260614/"
    "summary.json"
)
SELECTOR_CONTEXT_FEATURE_GAP_AUDIT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_context_feature_gap_audit_zh.md"
)
SELECTOR_FEATURE_AVAILABILITY_AUDIT_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_feature_availability_audit_20260614/"
    "summary.json"
)
SELECTOR_FEATURE_AVAILABILITY_AUDIT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_feature_availability_audit_zh.md"
)
CAPTURE_SCHEMA_FEASIBILITY_AUDIT_SUMMARY = Path(
    "BPC_future/results/root_cause_capture_schema_feasibility_audit_20260614/"
    "summary.json"
)
CAPTURE_SCHEMA_FEASIBILITY_AUDIT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_capture_schema_feasibility_audit_zh.md"
)
REMAINING_RMP_TRAJECTORY_FIELD_RECOVERY_SUMMARY = Path(
    "BPC_future/results/root_cause_remaining_rmp_trajectory_field_recovery_20260614/"
    "summary.json"
)
REMAINING_RMP_TRAJECTORY_FIELD_RECOVERY_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_remaining_rmp_trajectory_field_recovery_zh.md"
)
ACTIVE_BASIS_OBSERVABILITY_GAP_SUMMARY = Path(
    "BPC_future/results/root_cause_active_basis_observability_gap_20260614/"
    "summary.json"
)
ACTIVE_BASIS_OBSERVABILITY_GAP_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_active_basis_observability_gap_zh.md"
)
ACTIVE_BASIS_CAPTURE_SCHEMA_FEASIBILITY_SUMMARY = Path(
    "BPC_future/results/root_cause_active_basis_capture_schema_feasibility_20260614/"
    "summary.json"
)
ACTIVE_BASIS_CAPTURE_SCHEMA_FEASIBILITY_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_active_basis_capture_schema_feasibility_zh.md"
)
ACTIVE_BASIS_SNAPSHOT_SMOKE_SUMMARY = Path(
    "BPC_future/results/root_cause_active_basis_snapshot_smoke_audit_20260614/"
    "summary.json"
)
ACTIVE_BASIS_SNAPSHOT_SMOKE_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_active_basis_snapshot_smoke_zh.md"
)
ACTIVE_BASIS_SNAPSHOT_MT20_SMOKE_SUMMARY = Path(
    "BPC_future/results/root_cause_active_basis_snapshot_mt20_smoke_audit_20260614/"
    "summary.json"
)
ACTIVE_BASIS_SNAPSHOT_MT20_SMOKE_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_active_basis_snapshot_mt20_smoke_zh.md"
)
ACTIVE_BASIS_SNAPSHOT_MULTI20_SMOKE_SUMMARY = Path(
    "BPC_future/results/root_cause_active_basis_snapshot_multi20_smoke_audit_20260614/"
    "summary.json"
)
ACTIVE_BASIS_SNAPSHOT_MULTI20_SMOKE_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_active_basis_snapshot_multi20_smoke_zh.md"
)
ACTIVE_BASIS_SNAPSHOT_GREEDY_APOLLO20_02_SMOKE_SUMMARY = Path(
    "BPC_future/results/"
    "root_cause_active_basis_snapshot_greedy_apollo20_02_smoke_audit_20260614/"
    "summary.json"
)
ACTIVE_BASIS_SNAPSHOT_GREEDY_APOLLO20_02_SMOKE_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_active_basis_snapshot_greedy_apollo20_02_smoke_zh.md"
)
ACTIVE_BASIS_SNAPSHOT_GREEDY20_PAIR_SMOKE_SUMMARY = Path(
    "BPC_future/results/root_cause_active_basis_snapshot_greedy20_pair_smoke_audit_20260614/"
    "summary.json"
)
ACTIVE_BASIS_SNAPSHOT_GREEDY20_PAIR_SMOKE_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_active_basis_snapshot_greedy20_pair_smoke_zh.md"
)
ACTIVE_BASIS_SNAPSHOT_SELECTOR_SIGNAL_SUMMARY = Path(
    "BPC_future/results/root_cause_active_basis_snapshot_selector_signal_20260614/"
    "summary.json"
)
ACTIVE_BASIS_SNAPSHOT_SELECTOR_SIGNAL_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_active_basis_snapshot_selector_signal_zh.md"
)
ACTIVE_BASIS_SNAPSHOT_COUNTEREXAMPLES_SUMMARY = Path(
    "BPC_future/results/root_cause_active_basis_snapshot_counterexamples_20260614/"
    "summary.json"
)
ACTIVE_BASIS_SNAPSHOT_COUNTEREXAMPLES_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_active_basis_snapshot_counterexamples_zh.md"
)
SELECTOR_ENRICHED_RMP_FEATURE_HOLDOUT_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_enriched_rmp_feature_holdout_20260614/"
    "summary.json"
)
SELECTOR_ENRICHED_RMP_FEATURE_HOLDOUT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_enriched_rmp_feature_holdout_zh.md"
)
SELECTOR_ENRICHED_MULTIFEATURE_MODEL_HOLDOUT_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_enriched_multifeature_model_holdout_20260614/"
    "summary.json"
)
SELECTOR_ENRICHED_MULTIFEATURE_MODEL_HOLDOUT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_enriched_multifeature_model_holdout_zh.md"
)
PRODUCTION_AB_ENTRY_GATE_CATALOG_SUMMARY = Path(
    "BPC_future/results/root_cause_production_ab_entry_gate_catalog_20260614/"
    "summary.json"
)
PRODUCTION_AB_ENTRY_GATE_CATALOG_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_production_ab_entry_gate_catalog_zh.md"
)
OPTIMIZATION_DIRECTION_CANDIDATE_REGISTRY_SUMMARY = Path(
    "BPC_future/results/"
    "root_cause_optimization_direction_candidate_registry_20260614/"
    "summary.json"
)
OPTIMIZATION_DIRECTION_CANDIDATE_REGISTRY_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_optimization_direction_candidate_registry_zh.md"
)
SELECTOR_THRESHOLD_FRONTIER_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_threshold_frontier_20260613/summary.json"
)
SELECTOR_THRESHOLD_FRONTIER_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260613_bpc_future_root_cause_selector_threshold_frontier_zh.md"
)
SELECTOR_CONTEXT_COLLISION_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_context_collision_20260613/summary.json"
)
SELECTOR_CONTEXT_COLLISION_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260613_bpc_future_root_cause_selector_context_collision_zh.md"
)
SELECTOR_LOCAL_FEATURE_DIRECTION_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_local_feature_direction_20260613/"
    "summary.json"
)
SELECTOR_LOCAL_FEATURE_DIRECTION_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260613_bpc_future_root_cause_selector_local_feature_direction_zh.md"
)
SELECTOR_CONTEXT_DISAMBIGUATION_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_context_disambiguation_20260613/"
    "summary.json"
)
SELECTOR_CONTEXT_DISAMBIGUATION_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260613_bpc_future_root_cause_selector_context_disambiguation_zh.md"
)
SELECTOR_CONTEXT_SCALAR_CANDIDATES_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_context_scalar_candidates_20260613/"
    "summary.json"
)
SELECTOR_CONTEXT_SCALAR_CANDIDATES_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260613_bpc_future_root_cause_selector_context_scalar_candidates_zh.md"
)
SELECTOR_CONTEXT_SCALAR_HOLDOUT_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_context_scalar_holdout_20260613/"
    "summary.json"
)
SELECTOR_CONTEXT_SCALAR_HOLDOUT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260613_bpc_future_root_cause_selector_context_scalar_holdout_zh.md"
)
SELECTOR_MICRO_VS_FOLD_GATE_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_micro_vs_fold_gate_20260614/"
    "summary.json"
)
SELECTOR_MICRO_VS_FOLD_GATE_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_micro_vs_fold_gate_zh.md"
)
SELECTOR_MODEL_MICRO_VS_FOLD_GATE_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_model_micro_vs_fold_gate_20260614/"
    "summary.json"
)
SELECTOR_MODEL_MICRO_VS_FOLD_GATE_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_model_micro_vs_fold_gate_zh.md"
)
SELECTOR_RULE_FAMILY_SEARCH_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_rule_family_search_20260614/"
    "summary.json"
)
SELECTOR_RULE_FAMILY_SEARCH_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_rule_family_search_zh.md"
)
SELECTOR_RULE_FAMILY_SEARCH_20ONLY_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_rule_family_search_20only_20260614/"
    "summary.json"
)
SELECTOR_RULE_FAMILY_SEARCH_20ONLY_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_rule_family_search_20only_zh.md"
)
SELECTOR_RULE_FAMILY_TRAIN_HOLDOUT_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_rule_family_train_holdout_20260614/"
    "summary.json"
)
SELECTOR_RULE_FAMILY_TRAIN_HOLDOUT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_rule_family_train_holdout_zh.md"
)
SELECTOR_RULE_FAMILY_TRAIN_HOLDOUT_20ONLY_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_rule_family_train_holdout_20only_20260614/"
    "summary.json"
)
SELECTOR_RULE_FAMILY_TRAIN_HOLDOUT_20ONLY_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_rule_family_train_holdout_20only_zh.md"
)
SELECTOR_CONTEXT_FOLD_ANATOMY_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_context_fold_anatomy_20260614/"
    "summary.json"
)
SELECTOR_CONTEXT_FOLD_ANATOMY_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_context_fold_anatomy_zh.md"
)
SELECTOR_CONTEXT_FEATURE_ANATOMY_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_context_feature_anatomy_20260614/"
    "summary.json"
)
SELECTOR_CONTEXT_FEATURE_ANATOMY_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_context_feature_anatomy_zh.md"
)
ROOT_CAUSE_CODE_BOUNDARY_SUMMARY = Path(
    "BPC_future/results/root_cause_code_boundary_20260613/summary.json"
)
ROOT_CAUSE_CODE_BOUNDARY_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260613_bpc_future_root_cause_code_boundary_zh.md"
)
ROOT_CAUSE_FAILURE_MATRIX_SUMMARY = Path(
    "BPC_future/results/root_cause_failure_matrix_20260613/summary.json"
)
ROOT_CAUSE_FAILURE_MATRIX_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260613_bpc_future_root_cause_failure_matrix_zh.md"
)
RESULTS_DIR = Path("BPC_future/results")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


BPC_FUTURE_PATH_REF_RE = re.compile(r"BPC_future/[^\s`\]\)\}\>\"'，。；：、]+")


def _document_path_reference_audit(paths: list[Path]) -> dict[str, Any]:
    references: list[dict[str, str]] = []
    missing: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for path in paths:
        if not path.exists():
            missing.append(
                {
                    "document": str(path),
                    "reference": str(path),
                    "reason": "document_missing",
                }
            )
            continue
        text = path.read_text(encoding="utf-8")
        for match in BPC_FUTURE_PATH_REF_RE.finditer(text):
            reference = match.group(0).rstrip(".,;:")
            key = (str(path), reference)
            if key in seen:
                continue
            seen.add(key)
            references.append({"document": str(path), "reference": reference})
            if not Path(reference).exists():
                missing.append(
                    {
                        "document": str(path),
                        "reference": reference,
                        "reason": "reference_missing",
                    }
                )
    return {
        "document_count": len(paths),
        "reference_count": len(references),
        "missing_references": missing,
        "all_references_exist": not missing,
    }


def _evidence_metric_value_is_populated(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, dict):
        return all(
            _evidence_metric_value_is_populated(item) for item in value.values()
        )
    if isinstance(value, list):
        return all(_evidence_metric_value_is_populated(item) for item in value)
    return True


def _as_int(value: Any) -> int:
    if value in (None, ""):
        return 0
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}


def _as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _root_cause_diagnosis_report_metrics(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    required_phrases = {
        "small_scale_overhead": "固定开销敏感",
        "returned_batch_selector": "addition-before 的 selector",
        "replay_selector_candidate_true": "has_replay_calibrated_selector_candidate = true",
        "task5_noop_guard": "has_task5_noop_no_regression_guard = true",
        "task10_noop_guard": "has_task10_noop_no_regression_guard = true",
        "task10_triggered_risk": "has_task10_triggered_regression_evidence = true",
        "full_5_10_ab_missing": "has_full_5_10_production_ab_evidence = false",
        "robust_selector_false": "has_robust_all_fold_selector = false",
        "production_selector_false": "has_production_validated_selector = false",
        "task5_noop_guard": "has_task5_noop_no_regression_guard",
        "task10_noop_guard": "has_task10_noop_no_regression_guard",
        "task10_triggered_risk": "has_task10_triggered_regression_evidence",
        "full_5_10_ab_missing": "has_full_5_10_production_ab_evidence",
        "task10_triggered_official_changed": "task10_triggered_official_changed = 61",
        "small_noop_not_success": "5/10 no-regression 目前只是 no-op gate 证据",
        "walltime_speedup_false": "has_20_walltime_speedup_evidence = false",
        "production_direction_false": "production_direction_proven = false",
        "not_complete": "当前目标不能标记完成",
        "target002_pt03_recovered": "pricing_time_limit=0.3",
        "target002_exact_coverage": "target_with_exact_capture_count = 3",
        "selector_shift": "has_replay_calibrated_selector_candidate = true",
        "selector_candidate_threshold": "true_reduced_cost <= -12.430587",
        "selector_candidate_not_production": "production_validated_selector = false",
        "active_worker_subroute_closed": "active_worker_subroute_closed = true",
        "do_not_open_certificate_gate": "do_not_open_certificate_gate = true",
        "trajectory_selector": "trajectory selector",
        "candidate_selector_models_fail": (
            "candidate selector models strict gate passing models = []"
        ),
        "matched_context_mixed": "matched-context strict mixed_group_count = 8",
        "exact_context_conflicts": "exact context conflict_group_count = 12",
        "calibration_only_until_selector_passes": (
            "calibration_only_until_selector_passes = true"
        ),
        "required_selector_holdouts": (
            "required_selector_holdouts = context / instance / dataset"
        ),
        "next_protocol_status": (
            "next_evidence_protocol_status = calibration_only_until_selector_passes"
        ),
        "next_protocol_catalog": "next_evidence_protocol_catalog = current",
        "current_stage_calibration_only": (
            "current_stage = calibration_only_selector_holdout"
        ),
        "selector_collection_schema_coverage": (
            "root_cause_selector_collection_schema_coverage = current"
        ),
        "selector_collection_schema_row_count": (
            "selector_collection_schema_row_count = 14"
        ),
        "selector_collection_schema_no_missing": (
            "selector_collection_schema_journey_missing_count = 0"
        ),
        "selector_holdout_collection_manifest": (
            "root_cause_selector_holdout_collection_manifest = current"
        ),
        "selector_holdout_collection_target_count": (
            "selector_holdout_collection_target_count = 10"
        ),
        "selector_holdout_collection_snapshot_gap": (
            "selector_holdout_targets_needing_active_basis_snapshot_count = 10"
        ),
        "selector_holdout_collection_runbook": (
            "root_cause_selector_holdout_collection_runbook = current"
        ),
        "selector_holdout_collection_runbook_commands": (
            "selector_holdout_collection_runbook_command_count = 6"
        ),
        "selector_holdout_collection_capture_audit": (
            "root_cause_selector_holdout_collection_capture_audit = current"
        ),
        "selector_holdout_collection_context_hits": (
            "selector_holdout_collection_expected_context_hit_count = 9"
        ),
        "selector_holdout_collection_not_ready": (
            "selector_holdout_collection_ready_for_selector_holdout = false"
        ),
        "selector_holdout_priority_collection_capture_audit": (
            "root_cause_selector_holdout_priority_collection_capture_audit = current"
        ),
        "selector_holdout_priority_collection_context_miss": (
            "selector_holdout_priority_collection_expected_context_hit_count = 0"
        ),
        "selector_holdout_priority_collection_not_ready": (
            "selector_holdout_priority_collection_ready_for_selector_holdout = false"
        ),
        "selector_holdout_priority_capture_miss": (
            "root_cause_selector_holdout_priority_capture_miss = current"
        ),
        "selector_holdout_priority_capture_miss_zero_hit": (
            "exact_hit_context_count = 0"
        ),
        "selector_holdout_target002_drift_audit": (
            "root_cause_selector_holdout_target002_drift_audit = current"
        ),
        "selector_holdout_target002_source_hit": (
            "selector_holdout_target002_drift_source_target_hit_count = 1"
        ),
        "selector_holdout_target002_new_miss": (
            "selector_holdout_target002_drift_new_target_hit_count = 0"
        ),
        "selector_holdout_target002_same_active": (
            "selector_holdout_target002_drift_new_same_active_event_count = 3"
        ),
        "selector_holdout_target002_probe_matrix": (
            "root_cause_selector_holdout_target002_probe_matrix = current"
        ),
        "selector_holdout_target002_probe_count": (
            "selector_holdout_target002_probe_matrix_probe_count = 5"
        ),
        "selector_holdout_target002_probe_recovered_zero": (
            "selector_holdout_target002_probe_matrix_target_recovered_probe_count = 0"
        ),
        "selector_holdout_target002_trajectory_branch": (
            "root_cause_selector_holdout_target002_trajectory_branch = current"
        ),
        "selector_holdout_target002_trajectory_same_active": (
            "selector_holdout_target002_trajectory_branch_same_active_event_count = 7"
        ),
        "selector_holdout_target002_trajectory_non_source": (
            "selector_holdout_target002_trajectory_branch_non_source_same_active_event_count = 6"
        ),
        "selector_context_sufficiency_gap": (
            "root_cause_selector_context_sufficiency_gap = current"
        ),
        "selector_context_sufficiency_status": (
            "selector_context_sufficiency_status = insufficient_for_production_selector"
        ),
        "selector_context_sufficiency_no_robust_single": (
            "selector_context_sufficiency_robust_single_feature_selector_count = 0"
        ),
        "selector_context_sufficiency_no_robust_model": (
            "selector_context_sufficiency_robust_multifeature_model_count = 0"
        ),
        "component_payload_addition_before_rows": (
            "component_payload_addition_before_rows_candidate_row_count = 48"
        ),
        "component_payload_explicit_forbidden": (
            "component_payload_addition_before_rows_explicit_forbidden_true_count = 48"
        ),
        "next_protocol_gates": (
            "next_evidence_protocol_gates = exact_context_capture_and_replay_dataset,addition_before_selector,production_candidate_ab"
        ),
        "capture_ready_status": (
            "exact_context_capture_and_replay_dataset = ready_for_selector_calibration_attempt"
        ),
        "addition_before_status": (
            "addition_before_selector = calibrated_candidate_available"
        ),
        "selector_holdout_blocked": "selector_holdout = not_production_validated",
        "production_ab_blocked": "production_candidate_ab = blocked",
        "capture_ready_cases": "ready_case_count = 70",
        "base_capture_status_not_selector_rows": (
            "不是最终 selector dataset 的行数"
        ),
        "selector_dataset_280_rows": "selector calibration dataset 扩展为",
        "capture_high_impact": "high_impact_candidate_count = 143",
        "capture_noop": "noop_candidate_count = 59",
        "selector_false_positive": "selector_false_positive_count = 22",
        "selector_false_negative": "selector_false_negative_count = 31",
        "selector_error_anatomy": "selector_error_anatomy = current",
        "selector_fp_new_task_noop": (
            "false_positive_new_task_set_noop_count = 21"
        ),
        "selector_fn_new_task_improved": (
            "false_negative_new_task_set_improved_count = 23"
        ),
        "selector_threshold_frontier": "selector_threshold_frontier = current",
        "selector_threshold_no_perfect": "perfect_threshold_count = 0",
        "selector_threshold_zero_fp_recall": (
            "best_zero_false_positive_recall = 0.267942583732"
        ),
        "selector_threshold_zero_fn_fp": "best_zero_false_negative_fp = 62",
        "selector_context_collision": "selector_context_collision = current",
        "selector_context_task_set_mixed": "task_set_mixed_group_count = 6",
        "selector_context_sequence_mixed": "task_sequence_mixed_group_count = 5",
        "selector_context_online_flags_mixed": "online_flags_mixed_row_count = 278",
        "selector_local_feature_direction": (
            "selector_local_feature_direction = current"
        ),
        "selector_local_task_set_true_rc": (
            "task_set_true_rc_direction_counts = {'improved_lower_mean': 2, 'noop_lower_mean': 4}"
        ),
        "selector_local_sequence_true_rc": (
            "task_sequence_true_rc_direction_counts = {'noop_lower_mean': 3, 'improved_lower_mean': 2}"
        ),
        "selector_context_disambiguation": (
            "selector_context_disambiguation = current"
        ),
        "context_disambig_local_sequence_mixed": (
            "local_sequence_mixed_group_count = 5"
        ),
        "context_disambig_context_hash_zero": (
            "local_sequence_online_context_hash_mixed_group_count = 0"
        ),
        "context_hash_not_selector": (
            "context_hash 本身太具体，不能直接作为 production selector"
        ),
        "selector_context_scalar_candidates": (
            "selector_context_scalar_candidates = current"
        ),
        "control_objective_bin_zero": (
            "control_objective_bin_100_mixed_group_count = 0"
        ),
        "control_objective_holdout_required": (
            "它仍是 calibration 线索，不是 production selector"
        ),
        "selector_context_scalar_holdout": (
            "selector_context_scalar_holdout = current"
        ),
        "control_objective_holdout_zero": (
            "control_objective_holdout_passing_model_count = 0"
        ),
        "control_objective_holdout_not_production": (
            "control_objective_holdout_production_validated_selector = false"
        ),
        "selector_micro_vs_fold_gate": (
            "selector_micro_vs_fold_gate = current"
        ),
        "micro_vs_fold_robust_zero": (
            "robust_all_fold_passing_feature_count = 0"
        ),
        "selector_model_micro_vs_fold_gate": (
            "selector_model_micro_vs_fold_gate = current"
        ),
        "model_micro_vs_fold_robust_zero": (
            "robust_all_fold_passing_model_count = 0"
        ),
        "selector_rule_family_search": (
            "selector_rule_family_search = current"
        ),
        "rule_family_rule_count": "rule_family_rule_count = 18887",
        "rule_family_material_zero": (
            "rule_family_material_all_fold_passing_rule_count = 0"
        ),
        "selector_rule_family_search_20only": (
            "selector_rule_family_search_20only = current"
        ),
        "rule_family_20only_rule_count": (
            "rule_family_20only_rule_count = 18901"
        ),
        "rule_family_20only_material_zero": (
            "rule_family_20only_material_all_fold_passing_rule_count = 0"
        ),
        "selector_rule_family_train_holdout": (
            "selector_rule_family_train_holdout = current"
        ),
        "rule_family_train_context_folds": (
            "rule_family_train_context_material_passing_folds = 17/28"
        ),
        "selector_rule_family_train_holdout_20only": (
            "selector_rule_family_train_holdout_20only = current"
        ),
        "rule_family_train_20only_context_folds": (
            "rule_family_train_20only_context_material_passing_folds = 17/27"
        ),
        "selector_context_fold_anatomy": (
            "selector_context_fold_anatomy = current"
        ),
        "context_anatomy_false_positive_no_positive": (
            "context_fold_anatomy_twenty_false_positive_no_positive_context_count = 4"
        ),
        "context_anatomy_missed_positive": (
            "context_fold_anatomy_twenty_missed_positive_context_count = 3"
        ),
        "selector_context_feature_anatomy": (
            "selector_context_feature_anatomy = current"
        ),
        "context_feature_mixed_instance": (
            "context_feature_mixed_instance_group_count = 2"
        ),
        "context_feature_mixed_dataset": (
            "context_feature_mixed_dataset_group_count = 2"
        ),
        "selector_collection_schema_coverage": (
            "root_cause_selector_collection_schema_coverage = current"
        ),
        "selector_collection_schema_row_count": (
            "selector_collection_schema_row_count = 14"
        ),
        "selector_collection_schema_no_missing": (
            "selector_collection_schema_journey_missing_count = 0"
        ),
        "selector_holdout_collection_manifest": (
            "root_cause_selector_holdout_collection_manifest = current"
        ),
        "selector_holdout_collection_target_count": (
            "selector_holdout_collection_target_count = 10"
        ),
        "selector_holdout_collection_snapshot_gap": (
            "selector_holdout_targets_needing_active_basis_snapshot_count = 10"
        ),
        "selector_holdout_collection_runbook": (
            "root_cause_selector_holdout_collection_runbook = current"
        ),
        "selector_holdout_collection_runbook_commands": (
            "selector_holdout_collection_runbook_command_count = 6"
        ),
        "selector_holdout_collection_capture_audit": (
            "root_cause_selector_holdout_collection_capture_audit = current"
        ),
        "selector_holdout_collection_context_hits": (
            "selector_holdout_collection_expected_context_hit_count = 9"
        ),
        "selector_holdout_collection_not_ready": (
            "selector_holdout_collection_ready_for_selector_holdout = false"
        ),
        "selector_holdout_target002_drift_audit": (
            "root_cause_selector_holdout_target002_drift_audit = current"
        ),
        "selector_holdout_target002_source_hit": (
            "selector_holdout_target002_drift_source_target_hit_count = 1"
        ),
        "selector_holdout_target002_new_miss": (
            "selector_holdout_target002_drift_new_target_hit_count = 0"
        ),
        "selector_holdout_target002_same_active": (
            "selector_holdout_target002_drift_new_same_active_event_count = 3"
        ),
        "selector_holdout_target002_probe_matrix": (
            "root_cause_selector_holdout_target002_probe_matrix = current"
        ),
        "selector_holdout_target002_probe_count": (
            "selector_holdout_target002_probe_matrix_probe_count = 5"
        ),
        "selector_holdout_target002_probe_recovered_zero": (
            "selector_holdout_target002_probe_matrix_target_recovered_probe_count = 0"
        ),
        "selector_holdout_target002_trajectory_branch": (
            "root_cause_selector_holdout_target002_trajectory_branch = current"
        ),
        "selector_holdout_target002_trajectory_same_active": (
            "selector_holdout_target002_trajectory_branch_same_active_event_count = 7"
        ),
        "selector_holdout_target002_trajectory_non_source": (
            "selector_holdout_target002_trajectory_branch_non_source_same_active_event_count = 6"
        ),
        "selector_context_sufficiency_gap": (
            "root_cause_selector_context_sufficiency_gap = current"
        ),
        "selector_context_sufficiency_status": (
            "selector_context_sufficiency_status = insufficient_for_production_selector"
        ),
        "selector_context_sufficiency_no_robust_single": (
            "selector_context_sufficiency_robust_single_feature_selector_count = 0"
        ),
        "selector_context_sufficiency_no_robust_model": (
            "selector_context_sufficiency_robust_multifeature_model_count = 0"
        ),
        "production_selector_blocker_catalog": (
            "production_selector_blocker_catalog = current"
        ),
        "production_selector_blocker_status": (
            "production_selector_status = production_selector_not_validated"
        ),
        "production_selector_blocker_ids": (
            "production_selector_blocker_ids = concrete_false_positive_and_false_negative_examples,micro_average_gate_not_fold_stable,aggregate_model_gate_not_fold_stable,simple_rule_family_has_no_all_fold_rule,train_holdout_rules_not_context_stable,context_anatomy_has_opposite_failure_modes"
        ),
        "production_selector_blocker_checks": (
            "production_selector_blocker_all_checks_pass = true"
        ),
        "production_ab_entry_gate_catalog": (
            "production_ab_entry_gate_catalog = current"
        ),
        "production_ab_entry_status": (
            "production_candidate_ab_entry_status = blocked"
        ),
        "production_ab_entry_blockers": (
            "entry_gate_blockers = selector_not_validated,five_ten_full_no_regression_missing,twenty_speedup_missing"
        ),
        "production_ab_no_worker_default": (
            "must_not_enable_worker_default = true"
        ),
        "production_ab_no_certificate_gate": (
            "must_not_open_certificate_gate = true"
        ),
        "production_ab_selector_holdout_required": (
            "requires_selector_holdout_before_ab = true"
        ),
        "production_ab_forbidden_shortcuts": (
            "forbidden_shortcuts = post_addition_or_hindsight_features,single_context_replay_success,worker_negative_columns_without_walltime_roi,certificate_effect"
        ),
        "active_basis_capture_schema_feasibility": (
            "active_basis_capture_schema_feasibility = current"
        ),
        "active_basis_capture_all_fields_feasible": (
            "active_basis_capture_feasible_target_schema_field_count = 9"
        ),
        "active_basis_capture_no_missing_fields": (
            "active_basis_capture_missing_target_schema_field_count = 0"
        ),
        "active_basis_capture_no_certificate_effect": (
            "active_basis_capture_requires_certificate_effect = false"
        ),
        "active_basis_capture_supports_snapshot": (
            "active_basis_capture_supports_active_basis_snapshot = true"
        ),
        "active_basis_capture_implemented_default_off": (
            "active_basis_capture_schema_implementation_status = implemented_default_off"
        ),
        "robust_rule_selector_false": (
            "has_robust_all_fold_rule_selector = false"
        ),
        "robust_selector_available_false": (
            "robust_all_fold_selector_available = false"
        ),
        "failure_matrix_current": "failure_matrix = current",
        "failure_matrix_route_count": "failure_matrix_route_count = 7",
        "failure_matrix_ruled_out_count": (
            "failure_matrix_blocked_or_ruled_out_route_count = 7"
        ),
        "failure_matrix_route_text": (
            "它把“做了很多为什么仍不行”拆成 7 条路线"
        ),
        "why_many_attempts_failed_current": "why_many_attempts_failed = current",
        "why_many_attempts_failed_status": (
            "why_many_attempts_failed_status = supported_but_optimization_direction_unproven"
        ),
        "why_many_attempts_failed_primary_causes": (
            "why_many_attempts_failed_primary_causes = small_scale_fixed_overhead_sensitivity,twenty_returned_batch_rmp_trajectory_coupling,addition_before_selector_not_production_validated"
        ),
        "why_many_attempts_failed_ruled_out_count": (
            "why_many_attempts_failed_ruled_out_hypothesis_count = 5"
        ),
        "broad_dataset_holdout_zero": "broad_dataset_holdout_pass_count = 0",
        "broad_instance_holdout_zero": "broad_instance_holdout_pass_count = 0",
        "capture_default_disabled": (
            "counterfactual_replay_capture_default_enabled = false"
        ),
        "capture_diagnostic_only": (
            "counterfactual_replay_capture_diagnostic_only = true"
        ),
        "capture_not_certificate_capable": (
            "counterfactual_replay_capture_certificate_capable = false"
        ),
        "capture_no_official_bound_effect": (
            "counterfactual_replay_capture_official_bound_effect = false"
        ),
        "profile_priority_default_empty": (
            "profile_priority_task_masks_default_empty = true"
        ),
        "profile_priority_min_default_zero": (
            "profile_priority_min_returned_default_zero = true"
        ),
        "code_boundary_audit": "code_boundary_audit = current",
        "code_boundary_capture_guarded": (
            "counterfactual_capture_guarded_by_config = true"
        ),
        "code_boundary_profile_defaults": "profile_priority_defaults_empty = true",
        "code_boundary_experimental_profiles": (
            "experimental_profiles_not_default = true"
        ),
        "code_boundary_no_unvalidated_default": (
            "mainline_unvalidated_effect_default_enabled = false"
        ),
        "no_unvalidated_production_path": (
            "没有把任何未验证 selector / worker / certificate 逻辑默认接入 production path"
        ),
        "objective_requirement_audit": "objective_requirement_audit = current",
        "objective_completion_audit_catalog": (
            "objective_completion_audit_catalog = current"
        ),
        "evidence_bundle_manifest": (
            "root_cause_evidence_bundle_manifest = current"
        ),
        "evidence_bundle_rebuild": "root_cause_evidence_rebuild = current",
        "evidence_source_index_field": "evidence_source_index",
        "ruled_out_hypotheses_field": "ruled_out_hypotheses",
        "evidence_integrity_checks_field": "evidence_integrity_checks",
        "stable_document_claims_consistent": (
            "stable_document_claims_consistent = true"
        ),
        "primary_artifacts_all_exist": (
            "evidence_source_index_primary_artifacts_all_exist = true"
        ),
        "evidence_entries_complete": (
            "evidence_source_index_entries_structurally_complete = true"
        ),
        "document_path_refs_all_exist": (
            "root_cause_document_path_references_all_exist = true"
        ),
        "ruled_out_hypotheses_complete": (
            "ruled_out_hypotheses_structurally_complete = true"
        ),
        "missing_requirements_complete": (
            "missing_requirements_structurally_complete = true"
        ),
        "objective_audit_items_complete": (
            "objective_audit_items_structurally_complete = true"
        ),
        "next_evidence_protocol_complete": (
            "next_evidence_protocol_structurally_complete = true"
        ),
        "code_boundary_no_unvalidated_effect": (
            "code_boundary_no_unvalidated_production_effect = true"
        ),
        "ledger_self_consistency_pass": "ledger_self_consistency_pass = true",
        "completion_decision_field": "completion_decision",
        "root_cause_supported": "root_cause_explanation_supported = true",
        "objective_missing_production_selector": (
            "production_validated_selector = false"
        ),
        "objective_missing_five_ten_ab": (
            "five_ten_full_no_regression_ab = false"
        ),
        "objective_missing_twenty_speedup": "twenty_walltime_speedup = false",
        "objective_missing_requirements": (
            "missing_requirements = five_ten_full_no_regression_ab,production_validated_selector,twenty_walltime_speedup"
        ),
        "task10_triggered_official_changed": (
            "task10_triggered_official_changed = 61"
        ),
        "small_noop_not_worker_success": (
            "5/10 no-regression 目前只是 no-op gate 证据"
        ),
        "should_not_mark_complete": "should_mark_goal_complete = false",
    }
    phrase_presence = {
        key: phrase in text for key, phrase in required_phrases.items()
    }
    return {
        "source": str(path),
        "exists": path.exists(),
        "required_phrase_presence": phrase_presence,
        "check_root_cause_diagnosis_report_is_current": bool(
            path.exists() and all(phrase_presence.values())
        ),
    }


def _optimization_direction_readiness_report_metrics(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    stale_phrases = {
        "old_selector_row_count": "counterfactual_replay_selector_gate_row_count = 207",
        "old_exact_replay_rows": "207 rows",
        "old_exact_replay_rows_zh": "207 条 exact replay impact rows",
        "old_selector_flag": "has_stable_addition_before_selector",
        "old_true_rc_precision": "0.8513513513513513",
        "old_true_rc_recall": "0.8571428571428571",
        "old_target002_uncovered": "target002 remains uncovered",
        "old_target_coverage_count": "target_with_exact_capture_count = 2",
        "old_target002_uncovered_zh": "capture_target_002` 仍未覆盖",
        "old_target002_not_exact_covered_zh": "target002 仍未 exact covered",
        "old_target_coverage_count_zh": "3` 个 planned targets 中已有 `2`",
        "old_target_capture_event_count_zh": "104` 个 capture events 中已有 `2`",
    }
    required_phrases = {
        "last_review": "最后复核：2026-06-14",
        "purpose": "是否已经足够支持一个 production 优化方向",
        "root_cause_known": (
            "check_root_cause_known_but_optimization_direction_unproven = true"
        ),
        "robust_selector_false": "has_robust_all_fold_selector = false",
        "production_selector_false": "has_production_validated_selector = false",
        "walltime_speedup_false": "has_20_walltime_speedup_evidence = false",
        "production_direction_false": "production_direction_proven = false",
        "selector_candidate_rows": "exact_replay_selector_candidate_row_count = 280",
        "recommended_selector": (
            "recommended_selector_candidate = true_reduced_cost_<=_-12.430587"
        ),
        "with_target002_passing_feature_count": (
            "counterfactual_replay_selector_gate_with_target002_passing_feature_count = 4"
        ),
        "with_target002_passing_model_count": (
            "counterfactual_replay_model_selector_with_target002_all_holdout_passing_count = 2"
        ),
        "replay_local_not_production_flag": (
            "replay_local_selector_candidates_are_not_production = true"
        ),
        "replay_local_not_production_explanation": (
            "replay-local passing 不等于 production selector"
        ),
        "current_target_coverage_event_count": (
            "current_capture_target_coverage_event_count = 114"
        ),
        "current_target_exact_coverage_count": (
            "current_capture_target_exact_coverage_count = 3"
        ),
        "current_target_uncovered_zero": (
            "current_capture_target_uncovered_count = 0"
        ),
        "current_targets_all_covered": "current_capture_targets_all_covered = true",
        "rule_family_search": "selector_rule_family_search = current",
        "rule_family_zero": "rule_family_material_all_fold_passing_rule_count = 0",
        "rule_family_20only_zero": (
            "rule_family_20only_material_all_fold_passing_rule_count = 0"
        ),
        "train_context_folds": (
            "rule_family_train_context_material_passing_folds = 17/28"
        ),
        "train_20only_context_folds": (
            "rule_family_train_20only_context_material_passing_folds = 17/27"
        ),
        "context_fold_anatomy": "selector_context_fold_anatomy = current",
        "context_feature_anatomy": "selector_context_feature_anatomy = current",
        "context_feature_mixed_instance": (
            "context_feature_mixed_instance_group_count = 2"
        ),
        "context_feature_mixed_dataset": (
            "context_feature_mixed_dataset_group_count = 2"
        ),
        "cannot_say_production_direction": "已经找到了可上线优化方向",
        "next_gate": "selector 必须通过跨 dataset / 跨 instance gate",
    }
    phrase_presence = {
        key: phrase in text for key, phrase in required_phrases.items()
    }
    stale_phrase_presence = {
        key: phrase in text for key, phrase in stale_phrases.items()
    }
    return {
        "source": str(path),
        "exists": path.exists(),
        "required_phrase_presence": phrase_presence,
        "stale_phrase_presence": stale_phrase_presence,
        "check_optimization_direction_readiness_report_is_current": bool(
            path.exists()
            and all(phrase_presence.values())
            and not any(stale_phrase_presence.values())
        ),
    }


def _final_synthesis_report_metrics(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    stale_phrases = {
        "old_selector_row_count": "counterfactual_replay_selector_gate_row_count = 207",
        "old_exact_replay_rows": "207 rows",
        "old_exact_replay_rows_zh": "207 条 exact replay impact rows",
        "old_selector_flag": "has_stable_addition_before_selector",
        "old_true_rc_precision": "0.8513513513513513",
        "old_true_rc_recall": "0.8571428571428571",
        "old_target002_uncovered": "target002 remains uncovered",
        "old_target_coverage_count": "target_with_exact_capture_count = 2",
        "old_target002_uncovered_zh": "capture_target_002` 仍未覆盖",
        "old_target002_not_exact_covered_zh": "target002 仍未 exact covered",
        "old_target_coverage_count_zh": "3` 个 planned targets 中已有 `2`",
        "old_target_capture_event_count_zh": "104` 个 capture events 中已有 `2`",
    }
    required_phrases = {
        "title": "根因综合报告",
        "fixed_overhead": "固定开销",
        "task10_triggered_official_changed": "task10_triggered_official_changed = 61",
        "task10_triggered_worsened": "task10_triggered_worsened = 133",
        "small_noop_not_worker_success": "不是 worker/probe 本身已经有生产收益",
        "target002_exact_covered": "target_with_exact_capture_count = 3",
        "target002_uncovered_zero": "uncovered_target_count = 0",
        "target002_capture_event_count": "capture_event_count = 114",
        "returned_batch_selector": "addition 前判断 returned batch",
        "selector_candidate_rows": "当前 280 条 exact replay impact rows",
        "recommended_selector_precision": "full-sample precision 为 `0.89`",
        "recommended_selector_errors": "22` 个 false positives 和 `31` 个 false negatives",
        "micro_vs_fold_zero": "robust_all_fold_passing_feature_count = 0",
        "model_zero": "robust_all_fold_passing_model_count = 0",
        "rule_family_zero": "material_all_fold_passing_rule_count = 0",
        "rule_family_20only_zero": "20-task rows 后 `18901` 个规则中仍为 `0`",
        "train_context_folds": "context material folds 仍只有 `17/28`",
        "train_20only_context_folds": "20-only 仍只有 `17/27`",
        "context_failure_kinds": "4` 个 false-positive/no-positive contexts 和 `3` 个 missed-positive contexts",
        "context_feature_groups": "同一 instance 内有 `2` 组、同一 dataset 内有 `2` 组",
        "source_index_rule_family": "rule-family / context anatomy 排除简单 addition-before selector",
        "not_production_selector": "不能作为 production selector",
    }
    phrase_presence = {
        key: phrase in text for key, phrase in required_phrases.items()
    }
    stale_phrase_presence = {
        key: phrase in text for key, phrase in stale_phrases.items()
    }
    return {
        "source": str(path),
        "exists": path.exists(),
        "required_phrase_presence": phrase_presence,
        "stale_phrase_presence": stale_phrase_presence,
        "check_final_synthesis_report_is_current": bool(
            path.exists()
            and all(phrase_presence.values())
            and not any(stale_phrase_presence.values())
        ),
    }


def _requirement_audit_report_metrics(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    stale_phrases = {
        "old_selector_row_count": "counterfactual_replay_selector_gate_row_count = 207",
        "old_exact_replay_rows": "207 rows",
        "old_exact_replay_rows_zh": "207 条 exact replay impact rows",
        "old_selector_flag": "has_stable_addition_before_selector",
        "old_true_rc_precision": "0.8513513513513513",
        "old_true_rc_recall": "0.8571428571428571",
        "old_strict_selector_gate": "strict selector gate",
    }
    required_phrases = {
        "last_review": "最后复核：2026-06-14",
        "purpose": "目标逐项审计",
        "root_cause_explanation": "根因解释已经有强证据",
        "not_pulse_only": "这不是 Pulse 单点结论",
        "small_overhead": "triggered_worse_count = 220",
        "task10_triggered_risk": "task10_triggered_official_changed = 61",
        "small_noop_not_success": "5/10 no-regression 目前只是 no-op gate 证据",
        "worker_adds_not_solve": "pulse_worker_added_new_task_set_count = 8",
        "selector_candidate_rows": "exact_replay_selector_candidate_row_count = 280",
        "recommended_selector": (
            "recommended_selector_candidate = true_reduced_cost_<=_-12.430587"
        ),
        "recommended_errors": "recommended_selector_false_positive_count = 22",
        "micro_zero": "robust_all_fold_passing_feature_count = 0",
        "model_zero": "robust_all_fold_passing_model_count = 0",
        "rule_family": "selector_rule_family_search = current",
        "rule_family_zero": "rule_family_material_all_fold_passing_rule_count = 0",
        "rule_family_20only_zero": (
            "rule_family_20only_material_all_fold_passing_rule_count = 0"
        ),
        "train_context_folds": (
            "rule_family_train_context_material_passing_folds = 17/28"
        ),
        "train_20only_context_folds": (
            "rule_family_train_20only_context_material_passing_folds = 17/27"
        ),
        "context_feature": "selector_context_feature_anatomy = current",
        "context_feature_mixed_instance": (
            "context_feature_mixed_instance_group_count = 2"
        ),
        "context_feature_mixed_dataset": (
            "context_feature_mixed_dataset_group_count = 2"
        ),
        "goal_not_complete": "目标仍未完成",
        "no_mainline_default": "不打开 Pulse worker default",
        "local_signal_not_completion": "不能算完成，只能作为 calibration evidence",
    }
    phrase_presence = {
        key: phrase in text for key, phrase in required_phrases.items()
    }
    stale_phrase_presence = {
        key: phrase in text for key, phrase in stale_phrases.items()
    }
    return {
        "source": str(path),
        "exists": path.exists(),
        "required_phrase_presence": phrase_presence,
        "stale_phrase_presence": stale_phrase_presence,
        "check_requirement_audit_report_is_current": bool(
            path.exists()
            and all(phrase_presence.values())
            and not any(stale_phrase_presence.values())
        ),
    }


def _root_cause_current_answer_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    cause_ids = [
        str(cause.get("cause_id", "")) for cause in summary.get("confirmed_causes", [])
    ]
    missing = summary.get("missing_requirements", [])
    report_phrases = {
        "title": "BPC_future 根因当前答案" in report_text,
        "small_cause": "5/10 规模主要卡在固定开销敏感" in report_text,
        "twenty_cause": "20 规模不是没有 true-RC negative columns" in report_text,
        "selector_cause": "production-validated addition-before selector" in report_text,
        "keep_active": "completion_decision = keep_goal_active" in report_text,
        "goal_false": "goal_complete = false" in report_text,
        "missing_requirements": (
            "missing_requirements = "
            "five_ten_full_no_regression_ab,production_validated_selector,"
            "twenty_walltime_speedup"
        )
        in report_text,
        "production_gate_blocked": "production_ab_entry_gate = blocked" in report_text,
        "target002_probe_matrix": "target002 pt0.3" in report_text
        and "复现 probe 数为 0" in report_text,
        "target002_trajectory_branch": "同一 active hash" in report_text
        and "returned-batch composition 分叉" in report_text,
        "component_payload_rows": "component payload rows 结论" in report_text
        and "candidate_row_count" in report_text
        and "explicit_forbidden_true_count" in report_text,
        "component_payload_holdout_extension": (
            "component payload selector holdout extension 结论" in report_text
            and "combined_robust_feature_count" in report_text
            and "combined_robust_model_count" in report_text
        ),
        "worker_negative_roi_blocker": (
            "worker 负列 ROI 阻塞结论" in report_text
            and "worker_added_journeys" in report_text
            and "nonbaseline_worsened_rows" in report_text
            and "继续找更多或更负负列即可优化" in report_text
        ),
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "status": summary.get("status"),
        "cause_ids": cause_ids,
        "missing_requirements": missing,
        "completion_decision": summary.get("completion_decision"),
        "goal_complete": summary.get("goal_complete"),
        "production_ab_entry_gate": summary.get("production_ab_entry_gate"),
        "checks": checks,
        "report_phrase_presence": report_phrases,
        "check_root_cause_current_answer_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("diagnostic_only") is True
            and summary.get("runs_bpc_or_pricing") is False
            and summary.get("status")
            == "root_cause_supported_but_optimization_direction_unproven"
            and cause_ids
            == [
                "small_scale_fixed_overhead_sensitivity",
                "twenty_returned_batch_rmp_trajectory_coupling",
                "addition_before_selector_not_production_validated",
            ]
            and missing
            == [
                "five_ten_full_no_regression_ab",
                "production_validated_selector",
                "twenty_walltime_speedup",
            ]
            and summary.get("completion_decision") == "keep_goal_active"
            and summary.get("goal_complete") is False
            and summary.get("production_ab_entry_gate") == "blocked"
            and bool(checks.get("small_fixed_overhead_evidence_present"))
            and bool(checks.get("twenty_counterexample_evidence_present"))
            and bool(checks.get("worker_negative_roi_blocker_passed"))
            and bool(checks.get("selector_not_production_validated"))
            and bool(checks.get("target002_probe_matrix_passed"))
            and bool(checks.get("target002_trajectory_branch_passed"))
            and bool(checks.get("component_payload_rows_passed"))
            and bool(checks.get("component_payload_holdout_extension_passed"))
            and bool(checks.get("worker_default_forbidden"))
            and bool(checks.get("certificate_gate_forbidden"))
            and all(report_phrases.values())
        ),
    }


def _root_cause_causal_chain_audit_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    node_ids = [str(node.get("node_id", "")) for node in summary.get("causal_chain", [])]
    missing = summary.get("missing_requirements", [])
    expected_nodes = [
        "observed_requirements_not_met",
        "small_scale_fixed_overhead",
        "negative_columns_not_sufficient",
        "returned_batch_context_coupling",
        "selector_not_validated",
        "exact_context_not_recoverable_by_shortcut",
        "allowed_next_stage",
    ]
    expected_missing = [
        "five_ten_full_no_regression_ab",
        "production_validated_selector",
        "twenty_walltime_speedup",
    ]
    report_phrases = {
        "title": "Root Cause Causal Chain Audit 报告" in report_text,
        "current": "root_cause_causal_chain_audit = current" in report_text,
        "node_count": "causal_chain_node_count = 7" in report_text,
        "goal_false": "goal_complete = false" in report_text,
        "completion_keep_active": "completion_decision = keep_goal_active" in report_text,
        "production_direction_false": (
            "production_direction_approved = false" in report_text
        ),
        "small_node": "small_scale_fixed_overhead" in report_text,
        "negative_node": "negative_columns_not_sufficient" in report_text,
        "selector_node": "selector_not_validated" in report_text,
        "exact_context_node": "exact_context_not_recoverable_by_shortcut" in report_text,
        "blocked_conclusion": "production optimization direction 仍未获批" in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "status": summary.get("status"),
        "node_ids": node_ids,
        "missing_requirements": missing,
        "production_direction_approved": summary.get("production_direction_approved"),
        "goal_complete": summary.get("goal_complete"),
        "completion_decision": summary.get("completion_decision"),
        "checks": checks,
        "report_phrase_presence": report_phrases,
        "check_root_cause_causal_chain_audit_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("diagnostic_only") is True
            and summary.get("runs_bpc_or_pricing") is False
            and summary.get("status")
            == "causal_chain_supported_but_direction_unapproved"
            and node_ids == expected_nodes
            and missing == expected_missing
            and summary.get("production_direction_approved") is False
            and summary.get("goal_complete") is False
            and summary.get("completion_decision") == "keep_goal_active"
            and checks.get("ledger_passed_and_goal_active") is True
            and checks.get("current_answer_passed") is True
            and checks.get("why_passed") is True
            and checks.get("direction_not_approved") is True
            and checks.get("small_cause_supported") is True
            and checks.get("negative_columns_not_sufficient") is True
            and checks.get("batch_context_coupling_supported") is True
            and checks.get("selector_not_validated") is True
            and checks.get("exact_context_shortcut_ruled_out") is True
            and all(report_phrases.values())
        ),
    }


def _root_cause_stale_claims_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "title": "Root Cause Stale Claim 审计报告" in report_text,
        "current": "root_cause_stale_claims = current" in report_text,
        "no_review": "needs_review_count = 0" in report_text,
        "no_unguarded": "未发现会把当前根因状态误写成 production-ready" in report_text,
    }
    checks = summary.get("checks", {})
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "status": summary.get("status"),
        "candidate_claim_count": _as_int(summary.get("candidate_claim_count")),
        "guarded_claim_count": _as_int(summary.get("guarded_claim_count")),
        "needs_review_count": _as_int(summary.get("needs_review_count")),
        "report_phrase_presence": report_phrases,
        "check_root_cause_stale_claims_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("diagnostic_only") is True
            and summary.get("runs_bpc_or_pricing") is False
            and summary.get("status") == "root_cause_stale_claims_audited"
            and _as_int(summary.get("candidate_claim_count")) > 0
            and _as_int(summary.get("needs_review_count")) == 0
            and checks.get("no_unguarded_stale_claims") is True
            and all(report_phrases.values())
        ),
    }


def _root_cause_missing_requirement_evidence_scan_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    positive_counts = summary.get("target_key_positive_counts", {})
    seen_counts = summary.get("target_key_seen_counts", {})
    report_phrases = {
        "title": "Missing Requirement Evidence Scan" in report_text,
        "current": "root_cause_missing_requirement_evidence_scan = current"
        in report_text,
        "zero_positive": "positive_claim_count = 0" in report_text,
        "no_claims": "没有任何字段声称" in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "status": summary.get("status"),
        "summary_file_count": _as_int(summary.get("summary_file_count")),
        "candidate_claim_count": _as_int(summary.get("candidate_claim_count")),
        "positive_claim_count": _as_int(summary.get("positive_claim_count")),
        "target_key_seen_counts": seen_counts,
        "target_key_positive_counts": positive_counts,
        "report_phrase_presence": report_phrases,
        "check_missing_requirement_evidence_scan_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("diagnostic_only") is True
            and summary.get("runs_bpc_or_pricing") is False
            and summary.get("status")
            == "root_cause_missing_requirement_evidence_scan_audited"
            and _as_int(summary.get("summary_file_count")) > 0
            and _as_int(summary.get("candidate_claim_count")) > 0
            and _as_int(summary.get("positive_claim_count")) == 0
            and all(_as_int(value) == 0 for value in positive_counts.values())
            and all(report_phrases.values())
        ),
    }


def _root_cause_next_action_plan_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    immediate_ids = [
        str(item.get("action_id", "")) for item in summary.get("immediate_actions", [])
    ]
    expected_immediate_ids = [
        "extend_no_certificate_effect_exact_context_replay",
        "fit_addition_before_selector_only",
        "require_all_holdout_pass_before_ab",
        "run_5_10_no_regression_before_20_speedup",
    ]
    expected_forbidden = [
        "default_enable_worker_or_audit",
        "increase_worker_budget_without_selector_roi",
        "open_official_certificate_gate",
        "treat_true_rc_or_new_task_set_as_selector",
        "use_post_addition_or_hindsight_features_online",
        "enter_production_ab_before_selector_holdout",
        "claim_goal_complete_without_5_10_and_20_ab",
    ]
    report_phrases = {
        "title": "Root Cause Next Action Plan 报告" in report_text,
        "current": "root_cause_next_action_plan = current" in report_text,
        "stage": "current_allowed_stage = calibration_only_selector_holdout"
        in report_text,
        "production_false": "production_direction_proven = false" in report_text,
        "goal_false": "goal_complete = false" in report_text,
        "holdouts": "required_selector_holdouts = context,instance,dataset"
        in report_text,
        "forbidden": "default_enable_worker_or_audit" in report_text
        and "increase_worker_budget_without_selector_roi" in report_text
        and "open_official_certificate_gate" in report_text,
        "worker_negative_roi_blocker": (
            "Worker Negative ROI Blocker" in report_text
            and "phase7o_nonbaseline_worsened_rows" in report_text
            and "phase7o_worker_added_journeys" in report_text
        ),
        "holdout_gap_mixed_zero": (
            '"complete_snapshot_mixed_context_count": 0' in report_text
        ),
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "status": summary.get("status"),
        "current_allowed_stage": summary.get("current_allowed_stage"),
        "production_direction_proven": summary.get("production_direction_proven"),
        "goal_complete": summary.get("goal_complete"),
        "missing_requirements": summary.get("missing_requirements"),
        "required_selector_holdouts": summary.get("required_selector_holdouts"),
        "immediate_action_ids": immediate_ids,
        "forbidden_actions": summary.get("forbidden_actions"),
        "selector_blocker_ids": summary.get("selector_blocker_ids"),
        "checks": checks,
        "report_phrase_presence": report_phrases,
        "check_root_cause_next_action_plan_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("diagnostic_only") is True
            and summary.get("runs_bpc_or_pricing") is False
            and summary.get("status") == "calibration_only_next_action"
            and summary.get("current_allowed_stage")
            == "calibration_only_selector_holdout"
            and summary.get("production_direction_proven") is False
            and summary.get("goal_complete") is False
            and summary.get("missing_requirements")
            == [
                "five_ten_full_no_regression_ab",
                "production_validated_selector",
                "twenty_walltime_speedup",
            ]
            and summary.get("required_selector_holdouts")
            == ["context", "instance", "dataset"]
            and immediate_ids == expected_immediate_ids
            and summary.get("forbidden_actions") == expected_forbidden
            and len(summary.get("selector_blocker_ids", [])) > 0
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _root_cause_document_consistency_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    metrics = summary.get("authoritative_metrics", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "title": "Root Cause Document Consistency 审计" in report_text,
        "mixed_zero": "complete_snapshot_mixed_context_count=0" in report_text,
        "worker_budget_forbidden": "increase_worker_budget_without_selector_roi"
        in report_text,
        "diagnostic_only": "diagnostic_only = true" in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "status": summary.get("status"),
        "authoritative_metrics": metrics,
        "checks": checks,
        "report_phrase_presence": report_phrases,
        "check_root_cause_document_consistency_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("diagnostic_only") is True
            and summary.get("runs_bpc_or_pricing") is False
            and summary.get("status") == "root_cause_documents_consistent"
            and _as_int(metrics.get("phase7o_nonbaseline_rows")) == 96
            and _as_int(metrics.get("phase7o_nonbaseline_worsened_rows")) == 96
            and _as_int(metrics.get("phase7o_worker_added_journeys")) == 63
            and _as_int(metrics.get("phase8q_worker_added_journeys")) == 10
            and _as_int(metrics.get("complete_snapshot_mixed_context_count")) == 0
            and _as_int(
                metrics.get("complete_explicit_forbidden_mixed_context_count")
            )
            == 0
            and checks.get("diagnosis_doc_has_current_metrics") is True
            and checks.get("target_doc_has_current_metrics") is True
            and checks.get("no_stale_mixed_context_count_claim") is True
            and checks.get("no_ambiguous_selector_holdout_blocked_claim") is True
            and all(report_phrases.values())
        ),
    }


def _root_cause_selector_collection_plan_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    target_ids = [
        str(item.get("target_id", ""))
        for item in summary.get("priority_context_targets", [])
    ]
    expected_target_ids = [
        "false_positive_no_positive_context",
        "missed_positive_context",
        "mixed_low_precision_or_recall_context",
    ]
    required_fields = list(summary.get("required_capture_fields", []))
    report_phrases = {
        "title": "Root Cause Selector Collection Plan 报告" in report_text,
        "current": "root_cause_selector_collection_plan = current" in report_text,
        "status": (
            "status = collect_no_certificate_effect_selector_holdout_data"
            in report_text
        ),
        "stage": "current_stage = calibration_only_selector_holdout" in report_text,
        "production_false": "production_direction_proven = false" in report_text,
        "active_basis_field": "`active_basis_churn_count_before`" in report_text,
        "degeneracy_field": "`rmp_degeneracy_pressure_before`" in report_text,
        "forbidden": "official certificate gate" in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "status": summary.get("status"),
        "current_stage": summary.get("current_stage"),
        "production_direction_proven": summary.get("production_direction_proven"),
        "target_ids": target_ids,
        "mixed_instance_target_count": len(summary.get("mixed_instance_targets", [])),
        "mixed_dataset_target_count": len(summary.get("mixed_dataset_targets", [])),
        "required_capture_fields": required_fields,
        "checks": checks,
        "report_phrase_presence": report_phrases,
        "check_root_cause_selector_collection_plan_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("diagnostic_only") is True
            and summary.get("runs_bpc_or_pricing") is False
            and summary.get("status")
            == "collect_no_certificate_effect_selector_holdout_data"
            and summary.get("current_stage") == "calibration_only_selector_holdout"
            and summary.get("production_direction_proven") is False
            and target_ids == expected_target_ids
            and len(summary.get("mixed_instance_targets", [])) >= 2
            and len(summary.get("mixed_dataset_targets", [])) >= 2
            and "active_basis_churn_count_before" in required_fields
            and "rmp_degeneracy_pressure_before" in required_fields
            and "official_effect_count" in required_fields
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _root_cause_selector_collection_schema_coverage_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "title": "Root Cause Selector Collection Schema Coverage 报告"
        in report_text,
        "current": (
            "root_cause_selector_collection_schema_coverage = current"
            in report_text
        ),
        "status": (
            "status = selector_collection_schema_covered_for_current_rows"
            in report_text
        ),
        "stage": "current_stage = calibration_only_selector_holdout" in report_text,
        "production_false": "production_direction_proven = false" in report_text,
        "returned_journeys": "`returned_journeys`" in report_text,
        "signature": "`signature`" in report_text,
        "service_start": "`service_start`" in report_text,
        "no_certificate_effect": "no-certificate-effect" in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "status": summary.get("status"),
        "current_stage": summary.get("current_stage"),
        "production_direction_proven": summary.get("production_direction_proven"),
        "row_count": summary.get("row_count"),
        "input_path_count": summary.get("input_path_count"),
        "csv_missing_count": summary.get("csv_missing_count"),
        "event_missing_count": summary.get("event_missing_count"),
        "journey_missing_count": summary.get("journey_missing_count"),
        "incomplete_journey_count": summary.get("incomplete_journey_count"),
        "signature_present_count": summary.get("signature_present_count"),
        "true_dual_hash_present_count": summary.get("true_dual_hash_present_count"),
        "returned_payload_present_count": summary.get(
            "returned_payload_present_count"
        ),
        "official_effect_event_bad_count": summary.get(
            "official_effect_event_bad_count"
        ),
        "audit_summary_bad_official_effect_count": summary.get(
            "audit_summary_bad_official_effect_count"
        ),
        "checks": checks,
        "report_phrase_presence": report_phrases,
        "check_root_cause_selector_collection_schema_coverage_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("diagnostic_only") is True
            and summary.get("runs_bpc_or_pricing") is False
            and summary.get("status")
            == "selector_collection_schema_covered_for_current_rows"
            and summary.get("current_stage") == "calibration_only_selector_holdout"
            and summary.get("production_direction_proven") is False
            and int(summary.get("row_count") or 0) >= 14
            and summary.get("csv_missing_count") == 0
            and summary.get("event_missing_count") == 0
            and summary.get("journey_missing_count") == 0
            and summary.get("incomplete_journey_count") == 0
            and summary.get("signature_present_count") == summary.get("row_count")
            and summary.get("true_dual_hash_present_count")
            == summary.get("row_count")
            and summary.get("returned_payload_present_count")
            == summary.get("row_count")
            and summary.get("official_effect_event_bad_count") == 0
            and summary.get("audit_summary_bad_official_effect_count") == 0
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _root_cause_selector_holdout_collection_manifest_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    failure_kind_counts = summary.get("failure_kind_counts", {})
    report_phrases = {
        "title": "Root Cause Selector Holdout Collection Manifest 报告"
        in report_text,
        "current": (
            "root_cause_selector_holdout_collection_manifest = current"
            in report_text
        ),
        "status": "status = selector_holdout_collection_manifest_ready"
        in report_text,
        "stage": "current_stage = calibration_only_selector_holdout" in report_text,
        "production_false": "production_direction_proven = false" in report_text,
        "target_count": "collection_target_count = 10" in report_text,
        "snapshot_gap": "targets_needing_active_basis_snapshot_count = 10"
        in report_text,
        "no_certificate_effect": "no-certificate-effect" in report_text,
        "forbidden": "official certificate gate" in report_text
        and "production BPC A/B before selector holdout" in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "status": summary.get("status"),
        "current_stage": summary.get("current_stage"),
        "production_direction_proven": summary.get("production_direction_proven"),
        "priority_context_count": summary.get("priority_context_count"),
        "collection_target_count": summary.get("collection_target_count"),
        "collection_target_candidate_row_count": summary.get(
            "collection_target_candidate_row_count"
        ),
        "targets_needing_active_basis_snapshot_count": summary.get(
            "targets_needing_active_basis_snapshot_count"
        ),
        "existing_active_basis_snapshot_anchor_count": summary.get(
            "existing_active_basis_snapshot_anchor_count"
        ),
        "failure_kind_counts": failure_kind_counts,
        "checks": checks,
        "report_phrase_presence": report_phrases,
        "check_root_cause_selector_holdout_collection_manifest_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("diagnostic_only") is True
            and summary.get("runs_bpc_or_pricing") is False
            and summary.get("status") == "selector_holdout_collection_manifest_ready"
            and summary.get("current_stage") == "calibration_only_selector_holdout"
            and summary.get("production_direction_proven") is False
            and summary.get("priority_context_count") == 10
            and summary.get("collection_target_count") == 10
            and int(summary.get("collection_target_candidate_row_count") or 0) >= 90
            and summary.get("targets_needing_active_basis_snapshot_count") == 10
            and int(summary.get("existing_active_basis_snapshot_anchor_count") or 0)
            >= 1
            and failure_kind_counts
            == {
                "false_positive_no_positive_context": 4,
                "missed_positive_context": 3,
                "mixed_low_precision_or_recall_context": 3,
            }
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _root_cause_selector_holdout_collection_runbook_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    commands = summary.get("commands", []) or []
    target_rows = summary.get("target_profile_rows", []) or []
    report_phrases = {
        "title": "Root Cause Selector Holdout Collection Runbook 报告" in report_text,
        "current": (
            "root_cause_selector_holdout_collection_runbook = current"
            in report_text
        ),
        "status": "status = selector_holdout_collection_runbook_ready" in report_text,
        "target_count": "collection_target_count = 10" in report_text,
        "command_count": "command_count = 6" in report_text,
        "source_config_class_count": "source_config_class_count = 2" in report_text,
        "component_payload_capture": "component payload 采集命令" in report_text,
        "forbidden_signature_capture": "forbidden-signature capture" in report_text,
        "not_run": "未执行这些命令" in report_text,
        "certificate_gate_closed": "未打开 worker default 或 certificate gate" in report_text,
    }
    command_text = "\n".join(str(item.get("command", "")) for item in commands)
    source_profiles = set(summary.get("source_profiles", []) or [])
    source_config_classes = set(summary.get("source_config_classes", []) or [])
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "status": summary.get("status"),
        "collection_target_count": summary.get("collection_target_count"),
        "collection_target_profile_mapping_count": summary.get(
            "collection_target_profile_mapping_count"
        ),
        "command_count": summary.get("command_count"),
        "source_profile_count": summary.get("source_profile_count"),
        "source_config_class_count": summary.get("source_config_class_count"),
        "source_config_classes": summary.get("source_config_classes"),
        "instance_count": summary.get("instance_count"),
        "unresolved_instances": summary.get("unresolved_instances"),
        "unsupported_profiles": summary.get("unsupported_profiles"),
        "unsupported_source_configs": summary.get("unsupported_source_configs"),
        "commands_path": str(summary_path.parent / "commands.sh"),
        "target_profile_rows_path": str(summary_path.parent / "target_profile_rows.csv"),
        "checks": checks,
        "report_phrase_presence": report_phrases,
        "check_root_cause_selector_holdout_collection_runbook_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and (summary_path.parent / "commands.sh").exists()
            and (summary_path.parent / "target_profile_rows.csv").exists()
            and summary.get("all_checks_pass") is True
            and summary.get("diagnostic_only") is True
            and summary.get("runs_bpc_or_pricing") is False
            and summary.get("status") == "selector_holdout_collection_runbook_ready"
            and summary.get("collection_target_count") == 10
            and len(target_rows) == 10
            and summary.get("command_count") == 6
            and summary.get("source_profile_count") == 3
            and summary.get("source_config_class_count") == 2
            and summary.get("instance_count") == 2
            and not summary.get("unresolved_instances")
            and not summary.get("unsupported_profiles")
            and not summary.get("unsupported_source_configs")
            and source_profiles
            == {
                "experimental_early_new_task_set_quota_3_20_only",
                "experimental_l1_previous_dual_stabilization_20_only",
                "experimental_pricing_time_0_6_20_only",
            }
            and source_config_classes
            == {
                "dp1000_pt02_cg4_tl8",
                "target002_pt03_dp1000_cg4_tl8",
            }
            and "--pricing-max-dp-states 1000" in command_text
            and "--pricing-time-limit 0.3" in command_text
            and "--pricing-time-limit 0.2" in command_text
            and "--max-cg-iterations 4" in command_text
            and "--counterfactual-replay-capture-active-basis" in command_text
            and "--counterfactual-replay-capture-active-basis-max-rows 0"
            in command_text
            and "--counterfactual-replay-capture-forbidden-signatures" in command_text
            and "--counterfactual-replay-capture-forbidden-signature-max-count 0"
            in command_text
            and checks.get("all_commands_have_forbidden_signature_capture") is True
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _root_cause_selector_holdout_collection_capture_audit_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    return _selector_holdout_collection_capture_audit_metrics(
        summary_path=summary_path,
        report_path=report_path,
        current_marker="root_cause_selector_holdout_collection_capture_audit = current",
        title="Root Cause Selector Holdout Collection Capture Audit 报告",
        expected_command_count=6,
        expected_capture_event_count=78,
        expected_context_hash_count=10,
        expected_context_hit_count=9,
        expected_context_complete_hit_count=9,
        expected_missing_context_count=1,
        check_key="check_root_cause_selector_holdout_collection_capture_audit_is_current",
    )


def _root_cause_selector_holdout_priority_collection_capture_audit_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    return _selector_holdout_collection_capture_audit_metrics(
        summary_path=summary_path,
        report_path=report_path,
        current_marker=(
            "root_cause_selector_holdout_priority_collection_capture_audit = current"
        ),
        title="Root Cause Selector Holdout Priority Collection Capture Audit 报告",
        expected_command_count=1,
        expected_capture_event_count=12,
        expected_context_hash_count=3,
        expected_context_hit_count=0,
        expected_context_complete_hit_count=0,
        expected_missing_context_count=3,
        check_key=(
            "check_root_cause_selector_holdout_priority_collection_capture_audit_is_current"
        ),
    )


def _selector_holdout_collection_capture_audit_metrics(
    *,
    summary_path: Path,
    report_path: Path,
    current_marker: str,
    title: str,
    expected_command_count: int,
    expected_capture_event_count: int,
    expected_context_hash_count: int,
    expected_context_hit_count: int,
    expected_context_complete_hit_count: int,
    expected_missing_context_count: int,
    check_key: str,
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "title": title in report_text,
        "current": current_marker in report_text,
        "status": (
            "status = selector_holdout_collection_capture_audited"
            in report_text
        ),
        "capture_event_count": (
            f"capture_event_count = {expected_capture_event_count}" in report_text
        ),
        "expected_context_hash_count": (
            f"expected_context_hash_count = {expected_context_hash_count}"
            in report_text
        ),
        "expected_context_hit_count": (
            f"expected_context_hit_count = {expected_context_hit_count}"
            in report_text
        ),
        "ready_false": "ready_for_selector_holdout = false" in report_text,
        "safe_no_certificate": "no_certificate_bad_count = 0" in report_text,
        "complete_active_basis": "active_basis_bad_count = 0" in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "status": summary.get("status"),
        "command_count": summary.get("command_count"),
        "capture_event_count": summary.get("capture_event_count"),
        "expected_context_hash_count": summary.get("expected_context_hash_count"),
        "expected_context_hit_count": summary.get("expected_context_hit_count"),
        "expected_context_complete_hit_count": summary.get(
            "expected_context_complete_hit_count"
        ),
        "missing_expected_context_count": summary.get(
            "missing_expected_context_count"
        ),
        "all_expected_contexts_hit": summary.get("all_expected_contexts_hit"),
        "all_expected_contexts_have_complete_snapshot": summary.get(
            "all_expected_contexts_have_complete_snapshot"
        ),
        "ready_for_selector_holdout": summary.get("ready_for_selector_holdout"),
        "no_certificate_bad_count": summary.get("no_certificate_bad_count"),
        "active_basis_bad_count": summary.get("active_basis_bad_count"),
        "checks": checks,
        "report_phrase_presence": report_phrases,
        check_key: bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("diagnostic_only") is True
            and summary.get("runs_bpc_or_pricing") is False
            and summary.get("status")
            == "selector_holdout_collection_capture_audited"
            and summary.get("command_count") == expected_command_count
            and summary.get("capture_event_count") == expected_capture_event_count
            and summary.get("expected_context_hash_count")
            == expected_context_hash_count
            and summary.get("expected_context_hit_count") == expected_context_hit_count
            and summary.get("expected_context_complete_hit_count")
            == expected_context_complete_hit_count
            and summary.get("missing_expected_context_count")
            == expected_missing_context_count
            and summary.get("all_expected_contexts_hit") is False
            and summary.get("all_expected_contexts_have_complete_snapshot") is False
            and summary.get("ready_for_selector_holdout") is False
            and summary.get("no_certificate_bad_count") == 0
            and summary.get("active_basis_bad_count") == 0
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _root_cause_selector_holdout_blocker_status_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    capture = summary.get("capture_status", {})
    collection = capture.get("collection", {})
    priority = capture.get("priority", {})
    mix = summary.get("snapshot_label_mix", {})
    base_rows = mix.get("base_selector_rows", {})
    complete_snapshot = mix.get("complete_snapshot", {})
    explicit_forbidden = mix.get("complete_explicit_forbidden", {})
    complete_snapshot_labels = complete_snapshot.get("label_counts", {})
    explicit_forbidden_labels = explicit_forbidden.get("label_counts", {})
    blockers = list(summary.get("production_entry_blockers", []))
    report_phrases = {
        "title": "Selector Holdout Blocker Status 报告" in report_text,
        "status": (
            "status = selector_holdout_blocked_by_snapshot_label_mix"
            in report_text
        ),
        "diagnostic": "runs_bpc_or_pricing = false" in report_text,
        "ordinary_capture": "capture_event_count=78" in report_text,
        "priority_capture": "capture_event_count=12" in report_text,
        "ordinary_context_hit": "9/10" in report_text,
        "priority_context_hit": "0/3" in report_text,
        "base_snapshot_zero": "complete_snapshot_row_count=0" in report_text,
        "complete_snapshot_mix": "59 improved / 3 noop" in report_text,
        "explicit_positive_only": "48 improved / 0 noop" in report_text,
        "production_blocked": "production BPC A/B 仍被阻塞" in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "status": summary.get("status"),
        "checks": checks,
        "collection_expected_context_hash_count": collection.get(
            "expected_context_hash_count"
        ),
        "collection_expected_context_hit_count": collection.get(
            "expected_context_hit_count"
        ),
        "collection_ready_for_selector_holdout": collection.get(
            "ready_for_selector_holdout"
        ),
        "priority_expected_context_hash_count": priority.get(
            "expected_context_hash_count"
        ),
        "priority_expected_context_hit_count": priority.get(
            "expected_context_hit_count"
        ),
        "priority_ready_for_selector_holdout": priority.get(
            "ready_for_selector_holdout"
        ),
        "base_selector_row_count": base_rows.get("row_count"),
        "base_complete_snapshot_row_count": base_rows.get(
            "complete_snapshot_row_count"
        ),
        "complete_snapshot_row_count": complete_snapshot.get("row_count"),
        "complete_snapshot_label_counts": complete_snapshot_labels,
        "complete_explicit_forbidden_row_count": explicit_forbidden.get("row_count"),
        "complete_explicit_forbidden_label_counts": explicit_forbidden_labels,
        "production_entry_blockers": blockers,
        "report_phrase_presence": report_phrases,
        "check_root_cause_selector_holdout_blocker_status_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("diagnostic_only") is True
            and summary.get("runs_bpc_or_pricing") is False
            and summary.get("status")
            == "selector_holdout_blocked_by_snapshot_label_mix"
            and collection.get("expected_context_hash_count") == 10
            and collection.get("expected_context_hit_count") == 9
            and collection.get("ready_for_selector_holdout") is False
            and priority.get("expected_context_hash_count") == 3
            and priority.get("expected_context_hit_count") == 0
            and priority.get("ready_for_selector_holdout") is False
            and base_rows.get("row_count") == 280
            and base_rows.get("complete_snapshot_row_count") == 0
            and complete_snapshot.get("row_count") == 62
            and complete_snapshot_labels.get("improved") == 59
            and complete_snapshot_labels.get("noop") == 3
            and explicit_forbidden.get("row_count") == 48
            and explicit_forbidden_labels.get("improved") == 48
            and "noop" not in explicit_forbidden_labels
            and set(
                [
                    "selector_not_validated",
                    "five_ten_full_no_regression_missing",
                    "twenty_speedup_missing",
                ]
            ).issubset(set(blockers))
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _root_cause_selector_holdout_priority_capture_miss_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "title": "Root Cause Selector Holdout Priority Capture Miss 报告"
        in report_text,
        "current": (
            "root_cause_selector_holdout_priority_capture_miss = current"
            in report_text
        ),
        "status": (
            "status = selector_holdout_priority_capture_miss_diagnosed"
            in report_text
        ),
        "expected_context_count": "expected_context_count = 3" in report_text,
        "exact_hit_context_count": "exact_hit_context_count = 0" in report_text,
        "source_active_hash_missing": (
            "source_active_hash_missing_context_count = 2" in report_text
        ),
        "same_active_component_drift": (
            "same_active_component_drift_context_count = 1" in report_text
        ),
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "status": summary.get("status"),
        "expected_context_count": summary.get("expected_context_count"),
        "exact_hit_context_count": summary.get("exact_hit_context_count"),
        "source_active_hash_missing_context_count": summary.get(
            "source_active_hash_missing_context_count"
        ),
        "same_active_component_drift_context_count": summary.get(
            "same_active_component_drift_context_count"
        ),
        "observed_event_count": summary.get("observed_event_count"),
        "observed_unique_context_count": summary.get("observed_unique_context_count"),
        "checks": checks,
        "report_phrase_presence": report_phrases,
        "check_root_cause_selector_holdout_priority_capture_miss_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("diagnostic_only") is True
            and summary.get("runs_bpc_or_pricing") is False
            and summary.get("status")
            == "selector_holdout_priority_capture_miss_diagnosed"
            and summary.get("expected_context_count") == 3
            and summary.get("exact_hit_context_count") == 0
            and summary.get("source_active_hash_missing_context_count") == 2
            and summary.get("same_active_component_drift_context_count") == 1
            and summary.get("observed_event_count") == 12
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _root_cause_worker_negative_column_roi_blocker_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    phase7o = summary.get("phase7o_expanded", {})
    phase8q = summary.get("phase8q_validation", {})
    phase7o_by_scale = phase7o.get("by_scale", {})
    phase7o_5 = phase7o_by_scale.get("5", {})
    phase7o_10 = phase7o_by_scale.get("10", {})
    phase7o_20 = phase7o_by_scale.get("20", {})
    report_phrases = {
        "title": "Worker Negative Column ROI Blocker 报告" in report_text,
        "status": (
            "status = worker_negative_columns_not_sufficient_for_roi"
            in report_text
        ),
        "diagnostic": "runs_bpc_or_pricing = false" in report_text,
        "phase7o_added": "worker_added_journeys\": 63" in report_text,
        "phase7o_new_task_sets": "worker_added_new_task_sets\": 30" in report_text,
        "phase7o_worsened": "nonbaseline_worsened_rows\": 96" in report_text,
        "phase8q_added": "worker_added_journeys\": 10" in report_text,
        "not_sufficient": "负列发现能力已经不是充分条件" in report_text,
        "selector_blocker": "低开销 addition-before selector" in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "status": summary.get("status"),
        "checks": checks,
        "phase7o_row_count": phase7o.get("row_count"),
        "phase7o_nonbaseline_rows": phase7o.get("nonbaseline_rows"),
        "phase7o_nonbaseline_worsened_rows": phase7o.get(
            "nonbaseline_worsened_rows"
        ),
        "phase7o_worker_added_journeys": phase7o.get("worker_added_journeys"),
        "phase7o_worker_added_new_task_sets": phase7o.get(
            "worker_added_new_task_sets"
        ),
        "phase7o_worker_added_support_changing": phase7o.get(
            "worker_added_support_changing"
        ),
        "phase7o_5_nonbaseline_worsened_rows": phase7o_5.get(
            "nonbaseline_worsened_rows"
        ),
        "phase7o_5_nonbaseline_rows": phase7o_5.get("nonbaseline_rows"),
        "phase7o_10_worker_added_journeys": phase7o_10.get(
            "worker_added_journeys"
        ),
        "phase7o_10_nonbaseline_worsened_rows": phase7o_10.get(
            "nonbaseline_worsened_rows"
        ),
        "phase7o_10_nonbaseline_rows": phase7o_10.get("nonbaseline_rows"),
        "phase7o_20_worker_added_journeys": phase7o_20.get(
            "worker_added_journeys"
        ),
        "phase7o_20_nonbaseline_improved_rows": phase7o_20.get(
            "nonbaseline_improved_rows"
        ),
        "phase8q_row_count": phase8q.get("row_count"),
        "phase8q_worker_added_rows": phase8q.get("worker_added_rows"),
        "phase8q_worker_added_journeys": phase8q.get("worker_added_journeys"),
        "phase8q_worker_added_new_task_sets": phase8q.get(
            "worker_added_new_task_sets"
        ),
        "phase8q_worker_added_support_changing": phase8q.get(
            "worker_added_support_changing"
        ),
        "phase8q_improved_without_worker_added_count": summary.get(
            "phase8q_improved_without_worker_added_count"
        ),
        "report_phrase_presence": report_phrases,
        "check_root_cause_worker_negative_column_roi_blocker_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("diagnostic_only") is True
            and summary.get("runs_bpc_or_pricing") is False
            and summary.get("status")
            == "worker_negative_columns_not_sufficient_for_roi"
            and phase7o.get("row_count") == 108
            and phase7o.get("nonbaseline_rows") == 96
            and phase7o.get("nonbaseline_worsened_rows") == 96
            and phase7o.get("worker_added_journeys") == 63
            and phase7o.get("worker_added_new_task_sets") == 30
            and phase7o.get("worker_added_support_changing") == 13
            and phase7o_5.get("nonbaseline_worsened_rows") == 16
            and phase7o_5.get("nonbaseline_rows") == 16
            and phase7o_10.get("worker_added_journeys") == 45
            and phase7o_10.get("nonbaseline_worsened_rows") == 56
            and phase7o_10.get("nonbaseline_rows") == 56
            and phase7o_20.get("worker_added_journeys") == 18
            and phase7o_20.get("nonbaseline_improved_rows") == 0
            and phase8q.get("row_count") == 35
            and phase8q.get("worker_added_rows") == 3
            and phase8q.get("worker_added_journeys") == 10
            and phase8q.get("worker_added_new_task_sets") == 8
            and phase8q.get("worker_added_support_changing") == 2
            and summary.get("phase8q_improved_without_worker_added_count") == 1
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _root_cause_selector_context_trajectory_protocol_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    exact_context_components = summary.get("exact_context_components", [])
    required_capture_payload = summary.get("required_capture_payload", [])
    priority_capture_miss_evidence = summary.get("priority_capture_miss_evidence", {})
    report_phrases = {
        "title": "Selector Context Trajectory Capture Protocol" in report_text,
        "current": (
            "root_cause_selector_context_trajectory_capture_protocol = current"
            in report_text
        ),
        "status": (
            "status = selector_context_trajectory_capture_protocol_ready"
            in report_text
        ),
        "source_profile_rerun_not_sufficient": (
            "source_profile_rerun_is_not_sufficient = true" in report_text
        ),
        "same_active_hash_not_sufficient": (
            "same_active_hash_is_not_sufficient = true" in report_text
        ),
        "exact_context_component_count": (
            "exact_context_component_count = 9" in report_text
        ),
        "required_capture_payload_count": (
            "required_capture_payload_count = 9" in report_text
        ),
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "status": summary.get("status"),
        "exact_context_component_count": len(exact_context_components),
        "required_capture_payload_count": len(required_capture_payload),
        "source_profile_rerun_is_not_sufficient": checks.get(
            "source_profile_rerun_is_not_sufficient"
        ),
        "same_active_hash_is_not_sufficient": checks.get(
            "same_active_hash_is_not_sufficient"
        ),
        "priority_capture_miss_expected_context_count": (
            priority_capture_miss_evidence.get("expected_context_count")
        ),
        "priority_capture_miss_exact_hit_context_count": (
            priority_capture_miss_evidence.get("exact_hit_context_count")
        ),
        "priority_capture_miss_source_active_hash_missing_context_count": (
            priority_capture_miss_evidence.get(
                "source_active_hash_missing_context_count"
            )
        ),
        "priority_capture_miss_same_active_component_drift_context_count": (
            priority_capture_miss_evidence.get(
                "same_active_component_drift_context_count"
            )
        ),
        "checks": checks,
        "report_phrase_presence": report_phrases,
        "check_root_cause_selector_context_trajectory_protocol_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("diagnostic_only") is True
            and summary.get("runs_bpc_or_pricing") is False
            and summary.get("status")
            == "selector_context_trajectory_capture_protocol_ready"
            and len(exact_context_components) == 9
            and len(required_capture_payload) == 9
            and checks.get("source_profile_rerun_is_not_sufficient") is True
            and checks.get("same_active_hash_is_not_sufficient") is True
            and priority_capture_miss_evidence.get("expected_context_count") == 3
            and priority_capture_miss_evidence.get("exact_hit_context_count") == 0
            and priority_capture_miss_evidence.get(
                "source_active_hash_missing_context_count"
            )
            == 2
            and priority_capture_miss_evidence.get(
                "same_active_component_drift_context_count"
            )
            == 1
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _root_cause_selector_holdout_context_worklist_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    action_counts = summary.get("recommended_action_counts", {})
    miss_counts = summary.get("priority_miss_class_counts", {})
    report_phrases = {
        "title": "Selector Holdout Context Worklist" in report_text,
        "current": "root_cause_selector_holdout_context_worklist = current"
        in report_text,
        "status": "status = selector_holdout_context_worklist_ready" in report_text,
        "unresolved": "unresolved_context_count = 5" in report_text,
        "same_profile_not_sufficient": (
            "same_profile_rerun_not_sufficient = true" in report_text
        ),
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "status": summary.get("status"),
        "row_count": summary.get("row_count"),
        "unresolved_context_count": summary.get("unresolved_context_count"),
        "actionable_context_count": summary.get("actionable_context_count"),
        "recommended_action_counts": action_counts,
        "priority_miss_class_counts": miss_counts,
        "checks": checks,
        "report_phrase_presence": report_phrases,
        "check_root_cause_selector_holdout_context_worklist_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("diagnostic_only") is True
            and summary.get("runs_bpc_or_pricing") is False
            and summary.get("status") == "selector_holdout_context_worklist_ready"
            and summary.get("row_count") == 12
            and summary.get("unresolved_context_count") == 5
            and summary.get("actionable_context_count") == 5
            and action_counts.get(
                "use_as_complete_snapshot_row_then_replay_label_if_needed"
            )
            == 7
            and action_counts.get(
                "do_not_repeat_same_source_profile_blindly_collect_trajectory_variants"
            )
            == 2
            and action_counts.get(
                "treat_current_rerun_as_near_miss_and_target_full_component_match"
            )
            == 1
            and action_counts.get(
                "unsupported_until_source_profile_or_instance_mapping_is_recovered"
            )
            == 1
            and miss_counts.get("source_active_hash_not_reached") == 2
            and miss_counts.get("same_active_but_returned_batch_or_component_drift")
            == 1
            and checks.get("same_profile_rerun_not_sufficient") is True
            and checks.get("production_direction_still_unproven") is True
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _root_cause_selector_holdout_context_action_plan_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    unresolved_counts = summary.get("unresolved_execution_category_counts", {})
    report_phrases = {
        "title": "Selector Holdout Context Action Plan" in report_text,
        "current": "root_cause_selector_holdout_context_action_plan = current"
        in report_text,
        "status": "status = selector_holdout_context_action_plan_ready"
        in report_text,
        "unresolved": "unresolved_action_count = 5" in report_text,
        "with_command": "unresolved_with_command_count = 4" in report_text,
        "without_command": "unresolved_without_command_count = 1" in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "status": summary.get("status"),
        "row_count": summary.get("row_count"),
        "complete_snapshot_action_count": summary.get(
            "complete_snapshot_action_count"
        ),
        "unresolved_action_count": summary.get("unresolved_action_count"),
        "unresolved_with_command_count": summary.get(
            "unresolved_with_command_count"
        ),
        "unresolved_without_command_count": summary.get(
            "unresolved_without_command_count"
        ),
        "unresolved_execution_category_counts": unresolved_counts,
        "checks": checks,
        "report_phrase_presence": report_phrases,
        "check_root_cause_selector_holdout_context_action_plan_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("diagnostic_only") is True
            and summary.get("runs_bpc_or_pricing") is False
            and summary.get("status")
            == "selector_holdout_context_action_plan_ready"
            and summary.get("row_count") == 12
            and summary.get("complete_snapshot_action_count") == 7
            and summary.get("unresolved_action_count") == 5
            and summary.get("unresolved_with_command_count") == 4
            and summary.get("unresolved_without_command_count") == 1
            and unresolved_counts.get("trajectory_variant_capture_required") == 2
            and unresolved_counts.get("full_component_match_required") == 1
            and unresolved_counts.get("run_or_reaudit_existing_manifest_command")
            == 1
            and unresolved_counts.get("source_mapping_recovery_required") == 1
            and checks.get("unresolved_count_matches_worklist") is True
            and checks.get("all_unresolved_have_closure_gate") is True
            and checks.get("blind_same_profile_rerun_not_allowed_as_closure")
            is True
            and checks.get("production_direction_still_unproven") is True
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _root_cause_selector_holdout_target002_drift_audit_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "title": "Root Cause Selector Holdout target002 Drift Audit 报告"
        in report_text,
        "current": (
            "root_cause_selector_holdout_target002_drift_audit = current"
            in report_text
        ),
        "status": (
            "status = selector_holdout_target002_context_drift_audited"
            in report_text
        ),
        "source_hit": "source_target_hit_count = 1" in report_text,
        "new_miss": "new_target_hit_count = 0" in report_text,
        "same_active": "new_same_active_event_count =" in report_text,
        "not_ready": "capture_audit_ready_for_selector_holdout = false"
        in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "status": summary.get("status"),
        "target_context_hash": summary.get("target_context_hash"),
        "target_active_hash": summary.get("target_active_hash"),
        "source_target_hit_count": summary.get("source_target_hit_count"),
        "new_target_hit_count": summary.get("new_target_hit_count"),
        "source_same_active_event_count": summary.get(
            "source_same_active_event_count"
        ),
        "new_same_active_event_count": summary.get("new_same_active_event_count"),
        "new_same_active_found_negative_count": summary.get(
            "new_same_active_found_negative_count"
        ),
        "new_same_active_incomplete_count": summary.get(
            "new_same_active_incomplete_count"
        ),
        "capture_audit_ready_for_selector_holdout": summary.get(
            "capture_audit_ready_for_selector_holdout"
        ),
        "shared_context_hashes": summary.get("shared_context_hashes"),
        "checks": checks,
        "report_phrase_presence": report_phrases,
        "check_root_cause_selector_holdout_target002_drift_audit_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("diagnostic_only") is True
            and summary.get("runs_bpc_or_pricing") is False
            and summary.get("status")
            == "selector_holdout_target002_context_drift_audited"
            and summary.get("target_context_hash") == "3f914a0d2b97fd27"
            and summary.get("target_active_hash") == "f0b96be45c5015c9"
            and summary.get("source_target_hit_count") == 1
            and summary.get("new_target_hit_count") == 0
            and int(summary.get("new_same_active_event_count") or 0) > 0
            and summary.get("capture_audit_ready_for_selector_holdout") is False
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _root_cause_selector_holdout_target002_probe_matrix_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "title": "Root Cause Selector Holdout target002 Probe Matrix 报告"
        in report_text,
        "current": (
            "root_cause_selector_holdout_target002_probe_matrix = current"
            in report_text
        ),
        "status": (
            "status = selector_holdout_target002_probe_matrix_audited"
            in report_text
        ),
        "source_hit": "source_target_hit_count = 1" in report_text,
        "target_not_recovered": "target_recovered_probe_count = 0" in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "status": summary.get("status"),
        "target_context_hash": summary.get("target_context_hash"),
        "probe_count": summary.get("probe_count"),
        "reproduction_probe_count": summary.get("reproduction_probe_count"),
        "source_target_hit_count": summary.get("source_target_hit_count"),
        "target_recovered_probe_count": summary.get("target_recovered_probe_count"),
        "target_recovered_probe_ids": summary.get("target_recovered_probe_ids"),
        "checks": checks,
        "report_phrase_presence": report_phrases,
        "check_root_cause_selector_holdout_target002_probe_matrix_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("diagnostic_only") is True
            and summary.get("runs_bpc_or_pricing") is False
            and summary.get("status")
            == "selector_holdout_target002_probe_matrix_audited"
            and summary.get("target_context_hash") == "3f914a0d2b97fd27"
            and summary.get("probe_count") == 5
            and summary.get("reproduction_probe_count") == 4
            and summary.get("source_target_hit_count") == 1
            and summary.get("target_recovered_probe_count") == 0
            and summary.get("target_recovered_probe_ids") == []
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _root_cause_selector_holdout_target002_trajectory_branch_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "title": "Root Cause Selector Holdout target002 Trajectory Branch 报告"
        in report_text,
        "current": (
            "root_cause_selector_holdout_target002_trajectory_branch = current"
            in report_text
        ),
        "status": (
            "status = selector_holdout_target002_trajectory_branch_audited"
            in report_text
        ),
        "same_active_count": "same_active_event_count =" in report_text,
        "non_source_count": "non_source_same_active_event_count =" in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "status": summary.get("status"),
        "target_context_hash": summary.get("target_context_hash"),
        "target_active_hash": summary.get("target_active_hash"),
        "same_active_event_count": summary.get("same_active_event_count"),
        "non_source_same_active_event_count": summary.get(
            "non_source_same_active_event_count"
        ),
        "same_active_context_hashes": summary.get("same_active_context_hashes"),
        "checks": checks,
        "report_phrase_presence": report_phrases,
        "check_root_cause_selector_holdout_target002_trajectory_branch_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("diagnostic_only") is True
            and summary.get("runs_bpc_or_pricing") is False
            and summary.get("status")
            == "selector_holdout_target002_trajectory_branch_audited"
            and summary.get("target_context_hash") == "3f914a0d2b97fd27"
            and summary.get("target_active_hash") == "f0b96be45c5015c9"
            and int(summary.get("same_active_event_count") or 0) > 0
            and int(summary.get("non_source_same_active_event_count") or 0) > 0
            and checks.get("same_active_has_pool_or_forbidden_signature_drift")
            is True
            and checks.get("same_active_has_objective_or_batch_drift") is True
            and checks.get("no_non_source_event_matches_target_context") is True
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _root_cause_selector_holdout_missing_context_diagnosis_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "title": "Root Cause Selector Holdout Missing Context Diagnosis 报告"
        in report_text,
        "current": "selector_holdout_missing_context_diagnosis = current"
        in report_text,
        "target": "target002_context_hash = 3f914a0d2b97fd27" in report_text,
        "not_ready": "ready_for_selector_holdout = false" in report_text,
        "not_recovered": "target002_target_recovered_probe_count = 0"
        in report_text,
        "branch": "context-trajectory 分叉" in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "status": summary.get("status"),
        "ready_for_selector_holdout": summary.get("ready_for_selector_holdout"),
        "missing_expected_context_count": summary.get(
            "missing_expected_context_count"
        ),
        "missing_context_hashes": summary.get("missing_context_hashes"),
        "target002_context_hash": summary.get("target002_context_hash"),
        "target002_target_recovered_probe_count": summary.get(
            "target002_target_recovered_probe_count"
        ),
        "target002_same_active_event_count": summary.get(
            "target002_same_active_event_count"
        ),
        "target002_non_source_same_active_event_count": summary.get(
            "target002_non_source_same_active_event_count"
        ),
        "checks": checks,
        "report_phrase_presence": report_phrases,
        "check_root_cause_selector_holdout_missing_context_diagnosis_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("diagnostic_only") is True
            and summary.get("runs_bpc_or_pricing") is False
            and summary.get("status")
            == "selector_holdout_missing_context_diagnosed"
            and summary.get("ready_for_selector_holdout") is False
            and summary.get("missing_expected_context_count") == 1
            and summary.get("missing_expected_complete_context_count") == 1
            and summary.get("missing_context_hashes") == ["3f914a0d2b97fd27"]
            and summary.get("target002_context_hash") == "3f914a0d2b97fd27"
            and summary.get("target002_missing_context_identified") is True
            and summary.get("target002_target_recovered_probe_count") == 0
            and int(summary.get("target002_same_active_event_count") or 0) > 0
            and int(summary.get("target002_non_source_same_active_event_count") or 0)
            > 0
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _root_cause_selector_holdout_target002_component_drift_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    field_same_counts = summary.get("field_same_counts", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "title": "Root Cause target002 Component Drift 报告" in report_text,
        "current": "selector_holdout_target002_component_drift = current"
        in report_text,
        "target": "target_context_hash = 3f914a0d2b97fd27" in report_text,
        "pool_zero": "pool_signature_hash_same_count = 0" in report_text,
        "forbidden_zero": "forbidden_signature_hash_same_count = 0"
        in report_text,
        "returned_zero": (
            "config_matched_exact_returned_task_sets_same_count = 0" in report_text
        ),
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "status": summary.get("status"),
        "target_context_hash": summary.get("target_context_hash"),
        "target_active_hash": summary.get("target_active_hash"),
        "non_source_same_active_event_count": summary.get(
            "non_source_same_active_event_count"
        ),
        "field_same_counts": field_same_counts,
        "config_matched_exact_returned_task_sets_same_count": summary.get(
            "config_matched_exact_returned_task_sets_same_count"
        ),
        "checks": checks,
        "report_phrase_presence": report_phrases,
        "check_root_cause_selector_holdout_target002_component_drift_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("diagnostic_only") is True
            and summary.get("runs_bpc_or_pricing") is False
            and summary.get("status")
            == "selector_holdout_target002_component_drift_diagnosed"
            and summary.get("target_context_hash") == "3f914a0d2b97fd27"
            and summary.get("target_active_hash") == "f0b96be45c5015c9"
            and int(summary.get("non_source_same_active_event_count") or 0) > 0
            and field_same_counts.get("pool_signature_hash") == 0
            and field_same_counts.get("forbidden_signature_hash") == 0
            and summary.get("config_matched_exact_returned_task_sets_same_count")
            == 0
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _root_cause_selector_component_feature_readiness_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "title": "Root Cause Selector Component Feature Readiness 报告"
        in report_text,
        "current": "selector_component_feature_readiness = current" in report_text,
        "status": "status = selector_component_features_not_production_ready"
        in report_text,
        "not_ready": "ready_for_selector_holdout = false" in report_text,
        "robust_zero": "robust_all_holdout_derived_feature_count = 0"
        in report_text
        and "robust_all_holdout_model_count = 0" in report_text,
        "forbidden_payload": "explicit_forbidden_signature_list_available_count = 18"
        in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "status": summary.get("status"),
        "row_count": summary.get("row_count"),
        "derived_feature_count": summary.get("derived_feature_count"),
        "robust_all_holdout_derived_feature_count": summary.get(
            "robust_all_holdout_derived_feature_count"
        ),
        "robust_all_holdout_model_count": summary.get(
            "robust_all_holdout_model_count"
        ),
        "explicit_forbidden_signature_list_available_count": summary.get(
            "explicit_forbidden_signature_list_available_count"
        ),
        "target002_pool_signature_same_count": summary.get(
            "target002_pool_signature_same_count"
        ),
        "target002_forbidden_signature_same_count": summary.get(
            "target002_forbidden_signature_same_count"
        ),
        "ready_for_selector_holdout": summary.get("ready_for_selector_holdout"),
        "required_feature_families": summary.get("required_feature_families"),
        "checks": checks,
        "report_phrase_presence": report_phrases,
        "check_root_cause_selector_component_feature_readiness_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("diagnostic_only") is True
            and summary.get("runs_bpc_or_pricing") is False
            and summary.get("status")
            == "selector_component_features_not_production_ready"
            and summary.get("row_count") == 280
            and summary.get("derived_feature_count") == 31
            and summary.get("robust_all_holdout_derived_feature_count") == 0
            and summary.get("robust_all_holdout_model_count") == 0
            and summary.get("explicit_forbidden_signature_list_available_count")
            == 18
            and summary.get("target002_pool_signature_same_count") == 0
            and summary.get("target002_forbidden_signature_same_count") == 0
            and summary.get("ready_for_selector_holdout") is False
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _root_cause_selector_component_capture_schema_contract_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "title": "Root Cause Selector Component Capture Schema Contract 报告"
        in report_text,
        "current": "selector_component_capture_schema_contract = current"
        in report_text,
        "status": "status = component_capture_schema_contract_audited"
        in report_text,
        "forbidden_available": "explicit_forbidden_signature_list_available = true"
        in report_text,
        "active_basis_complete": "complete_active_basis_events = 78"
        in report_text,
        "pool_complete": "complete_pool_events = 78" in report_text,
        "code_support": "code_supports_explicit_forbidden_payload = true"
        in report_text,
        "runbook_support": (
            "holdout_runbook_enables_explicit_forbidden_payload = true"
            in report_text
        ),
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "status": summary.get("status"),
        "capture_file_count": summary.get("capture_file_count"),
        "capture_event_count": summary.get("capture_event_count"),
        "complete_active_basis_events": summary.get(
            "complete_active_basis_events"
        ),
        "complete_pool_events": summary.get("complete_pool_events"),
        "returned_batch_complete_events": summary.get(
            "returned_batch_complete_events"
        ),
        "returned_batch_nonempty_events": summary.get(
            "returned_batch_nonempty_events"
        ),
        "forbidden_explicit_events": summary.get("forbidden_explicit_events"),
        "code_supports_explicit_forbidden_payload": summary.get(
            "code_supports_explicit_forbidden_payload"
        ),
        "holdout_runbook_enables_explicit_forbidden_payload": summary.get(
            "holdout_runbook_enables_explicit_forbidden_payload"
        ),
        "field_contract": summary.get("field_contract", []),
        "checks": checks,
        "report_phrase_presence": report_phrases,
        "check_root_cause_selector_component_capture_schema_contract_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("diagnostic_only") is True
            and summary.get("runs_bpc_or_pricing") is False
            and summary.get("status") == "component_capture_schema_contract_audited"
            and summary.get("capture_event_count") == 78
            and summary.get("complete_active_basis_events") == 78
            and summary.get("complete_pool_events") == 78
            and summary.get("returned_batch_complete_events") == 78
            and int(summary.get("returned_batch_nonempty_events") or 0) > 0
            and int(summary.get("forbidden_explicit_events") or 0) > 0
            and summary.get("code_supports_explicit_forbidden_payload") is True
            and summary.get("holdout_runbook_enables_explicit_forbidden_payload")
            is True
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _root_cause_component_payload_addition_before_rows_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    required_fields = [
        "active_basis_snapshot_complete_before",
        "candidate_forbidden_signature",
        "candidate_signature_in_pool",
        "explicit_forbidden_signature_list_available",
        "forbidden_signature_count_before",
        "forbidden_signature_payload_complete_before",
        "forbidden_signature_payload_count_before",
        "pool_candidate_task_freq_sum",
        "pool_candidate_task_set_max_jaccard",
        "returned_batch_forbidden_signature_count",
        "returned_batch_new_task_set_count",
        "returned_batch_size",
        "returned_batch_true_rc_gap_from_best",
        "returned_candidate_true_rc_rank",
    ]
    field_complete = summary.get("field_complete", {})
    report_phrases = {
        "title": "Root Cause Component Payload Addition-Before Rows 报告"
        in report_text,
        "current": "component_payload_addition_before_rows = current"
        in report_text,
        "candidate_count": "candidate_row_count = 48" in report_text,
        "explicit_forbidden": "explicit_forbidden_true_count = 48"
        in report_text,
        "calibration_only": "This is calibration evidence only" in report_text,
        "not_production_selector": "not a production selector" in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "status": summary.get("status"),
        "raw_capture_case_count": summary.get("raw_capture_case_count"),
        "ready_case_count": summary.get("ready_case_count"),
        "candidate_row_count": summary.get("candidate_row_count"),
        "high_impact_candidate_count": summary.get("high_impact_candidate_count"),
        "noop_candidate_count": summary.get("noop_candidate_count"),
        "explicit_forbidden_true_count": summary.get(
            "explicit_forbidden_true_count"
        ),
        "runs_local_rmp_replay": summary.get("runs_local_rmp_replay"),
        "candidate_rows_csv": summary.get("candidate_rows_csv"),
        "required_fields": required_fields,
        "checks": checks,
        "report_phrase_presence": report_phrases,
        "check_component_payload_addition_before_rows_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("diagnostic_only") is True
            and summary.get("runs_bpc_or_pricing") is False
            and summary.get("runs_local_rmp_replay") is True
            and summary.get("status") == "component_payload_addition_before_rows_audited"
            and summary.get("raw_capture_case_count") == 12
            and summary.get("ready_case_count") == 6
            and summary.get("candidate_row_count") == 48
            and summary.get("high_impact_candidate_count") == 48
            and summary.get("noop_candidate_count") == 0
            and summary.get("explicit_forbidden_true_count") == 48
            and all(checks.values())
            and all(field_complete.get(field) is True for field in required_fields)
            and all(report_phrases.values())
        ),
    }


def _root_cause_component_payload_selector_holdout_extension_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    base = summary.get("base", {}) if isinstance(summary.get("base"), dict) else {}
    component = (
        summary.get("component_only", {})
        if isinstance(summary.get("component_only"), dict)
        else {}
    )
    combined = (
        summary.get("combined", {}) if isinstance(summary.get("combined"), dict) else {}
    )
    report_phrases = {
        "title": "Root Cause Component Payload Selector Holdout Extension 报告"
        in report_text,
        "current": (
            "root_cause_component_payload_selector_holdout_extension = current"
            in report_text
        ),
        "base_row_count": "base_row_count = 280" in report_text,
        "component_row_count": "component_row_count = 48" in report_text,
        "combined_row_count": "combined_row_count = 328" in report_text,
        "positive_only": "component_positive_only = true" in report_text,
        "no_robust_feature": (
            "combined_robust_all_holdout_derived_feature_count = 0"
            in report_text
        ),
        "no_robust_model": (
            "combined_robust_all_holdout_model_count = 0" in report_text
        ),
        "not_production_selector": "还没有形成 production selector" in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "status": summary.get("status"),
        "base_row_count": base.get("row_count"),
        "component_row_count": component.get("row_count"),
        "combined_row_count": combined.get("row_count"),
        "component_positive_only": summary.get("component_positive_only"),
        "component_context_overlap_with_base_count": summary.get(
            "component_context_overlap_with_base_count"
        ),
        "component_context_new_count": summary.get("component_context_new_count"),
        "combined_robust_all_holdout_derived_feature_count": combined.get(
            "robust_all_holdout_derived_feature_count"
        ),
        "combined_robust_all_holdout_model_count": combined.get(
            "robust_all_holdout_model_count"
        ),
        "combined_best_context_model": combined.get("best_context_model"),
        "combined_best_context_model_context_folds": combined.get(
            "best_context_model_context_folds"
        ),
        "combined_best_context_model_instance_folds": combined.get(
            "best_context_model_instance_folds"
        ),
        "combined_best_context_model_dataset_folds": combined.get(
            "best_context_model_dataset_folds"
        ),
        "checks": checks,
        "report_phrase_presence": report_phrases,
        "check_component_payload_selector_holdout_extension_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("diagnostic_only") is True
            and summary.get("runs_bpc_or_pricing") is False
            and summary.get("status")
            == "component_payload_selector_holdout_extension_audited"
            and base.get("row_count") == 280
            and component.get("row_count") == 48
            and combined.get("row_count") == 328
            and summary.get("component_positive_only") is True
            and summary.get("combined_has_no_robust_selector") is True
            and combined.get("robust_all_holdout_derived_feature_count") == 0
            and combined.get("robust_all_holdout_model_count") == 0
            and combined.get("best_context_model_context_folds") == "18/30"
            and combined.get("best_context_model_instance_folds") == "4/4"
            and combined.get("best_context_model_dataset_folds") == "5/6"
            and summary.get("component_context_overlap_with_base_count") == 2
            and summary.get("component_context_new_count") == 2
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _root_cause_selector_context_sufficiency_gap_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "title": "Root Cause Selector Context Sufficiency Gap 报告"
        in report_text,
        "current": "root_cause_selector_context_sufficiency_gap = current"
        in report_text,
        "status": "status = selector_context_sufficiency_gap_audited"
        in report_text,
        "insufficient": (
            "selector_context_status = insufficient_for_production_selector"
            in report_text
        ),
        "no_robust_single": "robust_single_feature_selector_count = 0"
        in report_text,
        "no_robust_model": "robust_multifeature_model_count = 0"
        in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "status": summary.get("status"),
        "selector_context_status": summary.get("selector_context_status"),
        "same_active_event_count": summary.get("same_active_event_count"),
        "same_active_context_hash_count": summary.get("same_active_context_hash_count"),
        "non_source_same_active_event_count": summary.get(
            "non_source_same_active_event_count"
        ),
        "exact_disambiguator_fields_present_any": summary.get(
            "exact_disambiguator_fields_present_any"
        ),
        "aggregate_proxy_fields_present": summary.get("aggregate_proxy_fields_present"),
        "robust_single_feature_selector_count": summary.get(
            "robust_single_feature_selector_count"
        ),
        "robust_multifeature_model_count": summary.get(
            "robust_multifeature_model_count"
        ),
        "required_next_feature_families": summary.get("required_next_feature_families"),
        "checks": checks,
        "report_phrase_presence": report_phrases,
        "check_root_cause_selector_context_sufficiency_gap_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("diagnostic_only") is True
            and summary.get("runs_bpc_or_pricing") is False
            and summary.get("status") == "selector_context_sufficiency_gap_audited"
            and summary.get("selector_context_status")
            == "insufficient_for_production_selector"
            and int(summary.get("same_active_event_count") or 0) > 0
            and int(summary.get("same_active_context_hash_count") or 0) > 1
            and int(summary.get("non_source_same_active_event_count") or 0) > 0
            and summary.get("exact_disambiguator_fields_present_any") == []
            and summary.get("robust_single_feature_selector_count") == 0
            and summary.get("robust_multifeature_model_count") == 0
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _root_cause_selector_next_feature_gate_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    blocked_families = [
        item.get("family")
        for item in summary.get("blocked_feature_families", []) or []
    ]
    forbidden_next_actions = list(summary.get("forbidden_next_actions", []) or [])
    allowed_next_actions = list(summary.get("allowed_next_actions", []) or [])
    report_phrases = {
        "title": "Root Cause Selector Next Feature Gate 报告" in report_text,
        "current": "root_cause_selector_next_feature_gate = current" in report_text,
        "status": "status = selector_next_feature_gate_audited" in report_text,
        "blocked": (
            "selector_next_feature_gate_status = "
            "blocked_until_extended_context_features_and_holdout"
        )
        in report_text,
        "forbidden": "Forbidden Next Actions" in report_text,
    }
    expected_blocked = [
        "true_rc_threshold",
        "new_task_set_only",
        "active_basis_scalar_only",
        "current_enriched_single_or_multifeature_selector",
    ]
    expected_forbidden = [
        "default_worker",
        "official_certificate_gate",
        "production_bpc_ab_before_selector_holdout",
        "selector_using_post_addition_or_hindsight_features",
        "simple_true_rc_or_new_task_set_rule_as_production_gate",
    ]
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "status": summary.get("status"),
        "selector_next_feature_gate_status": summary.get(
            "selector_next_feature_gate_status"
        ),
        "blocked_feature_families": blocked_families,
        "allowed_next_actions": allowed_next_actions,
        "forbidden_next_actions": forbidden_next_actions,
        "false_positive_count": summary.get("false_positive_count"),
        "strongest_noop_true_reduced_cost": summary.get(
            "strongest_noop_true_reduced_cost"
        ),
        "robust_single_feature_selector_count": summary.get(
            "robust_single_feature_selector_count"
        ),
        "robust_multifeature_model_count": summary.get(
            "robust_multifeature_model_count"
        ),
        "collection_ready_for_selector_holdout": summary.get(
            "collection_ready_for_selector_holdout"
        ),
        "collection_missing_expected_context_count": summary.get(
            "collection_missing_expected_context_count"
        ),
        "checks": checks,
        "report_phrase_presence": report_phrases,
        "check_root_cause_selector_next_feature_gate_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("diagnostic_only") is True
            and summary.get("runs_bpc_or_pricing") is False
            and summary.get("status") == "selector_next_feature_gate_audited"
            and summary.get("selector_next_feature_gate_status")
            == "blocked_until_extended_context_features_and_holdout"
            and blocked_families == expected_blocked
            and forbidden_next_actions == expected_forbidden
            and summary.get("false_positive_count") == 2
            and summary.get("strongest_noop_true_reduced_cost") == -128.547499
            and summary.get("robust_single_feature_selector_count") == 0
            and summary.get("robust_multifeature_model_count") == 0
            and summary.get("collection_ready_for_selector_holdout") is False
            and summary.get("collection_missing_expected_context_count") == 1
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _root_cause_selector_pool_overlap_feature_probe_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "title": "Root Cause Selector Pool/Overlap Feature Probe 报告" in report_text,
        "current": "root_cause_selector_pool_overlap_feature_probe = current"
        in report_text,
        "status": "status = selector_pool_overlap_feature_probe_audited"
        in report_text,
        "no_robust_single": "robust_all_holdout_derived_feature_count = 0"
        in report_text,
        "no_robust_model": "robust_all_holdout_model_count = 0" in report_text,
        "forbidden_observed": (
            "explicit_forbidden_signature_list_available_count = 18" in report_text
        ),
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "status": summary.get("status"),
        "row_count": summary.get("row_count"),
        "manifest_case_count": summary.get("manifest_case_count"),
        "missing_manifest_join_count": summary.get("missing_manifest_join_count"),
        "derived_feature_count": summary.get("derived_feature_count"),
        "robust_all_holdout_derived_feature_count": summary.get(
            "robust_all_holdout_derived_feature_count"
        ),
        "robust_all_holdout_model_count": summary.get(
            "robust_all_holdout_model_count"
        ),
        "best_context_model": summary.get("best_context_model"),
        "best_context_model_context_folds": summary.get(
            "best_context_model_context_folds"
        ),
        "best_context_model_instance_folds": summary.get(
            "best_context_model_instance_folds"
        ),
        "best_context_model_dataset_folds": summary.get(
            "best_context_model_dataset_folds"
        ),
        "explicit_forbidden_signature_list_available_count": summary.get(
            "explicit_forbidden_signature_list_available_count"
        ),
        "checks": checks,
        "report_phrase_presence": report_phrases,
        "check_selector_pool_overlap_feature_probe_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("diagnostic_only") is True
            and summary.get("runs_bpc_or_pricing") is False
            and summary.get("status") == "selector_pool_overlap_feature_probe_audited"
            and summary.get("row_count") == 280
            and summary.get("missing_manifest_join_count") == 0
            and summary.get("derived_feature_count") == 31
            and summary.get("robust_all_holdout_derived_feature_count") == 0
            and summary.get("robust_all_holdout_model_count") == 0
            and summary.get("best_context_model_context_folds") == "17/28"
            and summary.get("best_context_model_instance_folds") == "4/4"
            and summary.get("best_context_model_dataset_folds") == "5/5"
            and summary.get("explicit_forbidden_signature_list_available_count") == 18
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _root_cause_selector_context_schema_gap_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    family_status = {
        item.get("family"): item.get("status")
        for item in summary.get("feature_family_status", []) or []
        if isinstance(item, dict)
    }
    report_phrases = {
        "title": "Root Cause Selector Context Schema Gap 报告" in report_text,
        "current": "root_cause_selector_context_schema_gap = current" in report_text,
        "status": "status = selector_context_schema_gap_audited" in report_text,
        "forbidden_observed": (
            "cases_with_explicit_forbidden_signature_list = 18" in report_text
        ),
        "feature_family_status": "Feature Family Status" in report_text,
    }
    expected_status = {
        "local_column_geometry": "available_but_blocked_as_production_selector_alone",
        "rmp_aggregate_context": "available_but_insufficient",
        "active_basis_full_snapshot_features": (
            "missing_from_current_replay_selector_rows"
        ),
        "pool_signature_composition_features": (
            "derivable_from_manifest_not_persisted_in_candidate_rows"
        ),
        "returned_batch_vs_pool_overlap_features": (
            "derivable_but_not_production_validated"
        ),
        "forbidden_signature_pressure_features": (
            "explicit_payload_available_not_production_validated"
        ),
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "status": summary.get("status"),
        "candidate_row_count": summary.get("candidate_row_count"),
        "manifest_case_count": summary.get("manifest_case_count"),
        "manifest_joined_row_count": summary.get("manifest_joined_row_count"),
        "complete_pool_payload_case_count": summary.get(
            "complete_pool_payload_case_count"
        ),
        "complete_returned_batch_case_count": summary.get(
            "complete_returned_batch_case_count"
        ),
        "active_basis_snapshot_complete_true_count": summary.get(
            "active_basis_snapshot_complete_true_count"
        ),
        "cases_with_explicit_forbidden_signature_list": summary.get(
            "cases_with_explicit_forbidden_signature_list"
        ),
        "feature_family_status": family_status,
        "checks": checks,
        "report_phrase_presence": report_phrases,
        "check_selector_context_schema_gap_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("diagnostic_only") is True
            and summary.get("runs_bpc_or_pricing") is False
            and summary.get("status") == "selector_context_schema_gap_audited"
            and summary.get("candidate_row_count") == 280
            and summary.get("manifest_case_count") == 122
            and summary.get("manifest_joined_row_count") == 280
            and summary.get("complete_pool_payload_case_count") == 122
            and summary.get("complete_returned_batch_case_count") == 122
            and summary.get("active_basis_snapshot_complete_true_count") == 0
            and summary.get("cases_with_explicit_forbidden_signature_list") == 18
            and all(checks.values())
            and all(report_phrases.values())
            and all(family_status.get(key) == value for key, value in expected_status.items())
        ),
    }


def _root_cause_selector_snapshot_sample_coverage_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "title": "Root Cause Selector Snapshot Sample Coverage 报告" in report_text,
        "current": "root_cause_selector_snapshot_sample_coverage = current"
        in report_text,
        "status": "status = selector_snapshot_sample_coverage_audited"
        in report_text,
        "holdout_not_ready": "holdout_ready = false" in report_text,
        "complete_snapshot_count": "complete_snapshot_row_count = 62" in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "status": summary.get("status"),
        "candidate_row_count": summary.get("candidate_row_count"),
        "combined_replay_selector_row_count": summary.get(
            "combined_replay_selector_row_count"
        ),
        "combined_replay_selector_complete_snapshot_row_count": summary.get(
            "combined_replay_selector_complete_snapshot_row_count"
        ),
        "complete_snapshot_row_count": summary.get("complete_snapshot_row_count"),
        "complete_snapshot_label_counts": summary.get(
            "complete_snapshot_label_counts"
        ),
        "complete_snapshot_source_class_counts": summary.get(
            "complete_snapshot_source_class_counts"
        ),
        "holdout_ready": summary.get("holdout_ready"),
        "checks": checks,
        "report_phrase_presence": report_phrases,
        "check_selector_snapshot_sample_coverage_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("diagnostic_only") is True
            and summary.get("runs_bpc_or_pricing") is False
            and summary.get("status")
            == "selector_snapshot_sample_coverage_audited"
            and summary.get("candidate_row_count") == 630
            and summary.get("combined_replay_selector_row_count") == 280
            and summary.get("combined_replay_selector_complete_snapshot_row_count")
            == 0
            and summary.get("complete_snapshot_row_count") == 62
            and summary.get("complete_snapshot_source_class_counts")
            == {
                "active_basis_snapshot_smoke": 14,
                "component_payload_addition_before_rows": 48,
            }
            and summary.get("holdout_ready") is False
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _goal_current_summary_metrics(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    current_section = text.split("\n---", 1)[0]
    required_phrases = {
        "stable_entry_doc": "BPC_future/docs/bpc_future_root_cause_diagnosis_zh.md",
        "stable_evidence_ledger": (
            "BPC_future/results/root_cause_evidence_ledger_20260613/summary.json"
        ),
        "evidence_source_index_current": "evidence_source_index = current",
        "ruled_out_hypotheses_current": "ruled_out_hypotheses = current",
        "evidence_integrity_checks_current": "evidence_integrity_checks = current",
        "objective_requirement_audit_current": "objective_requirement_audit = current",
        "objective_completion_audit_catalog_current": (
            "objective_completion_audit_catalog = current"
        ),
        "evidence_bundle_manifest_current": (
            "root_cause_evidence_bundle_manifest = current"
        ),
        "evidence_bundle_rebuild_current": (
            "root_cause_evidence_rebuild = current"
        ),
        "completion_decision_keep_active": "completion_decision = keep_goal_active",
        "missing_requirements_current": (
            "missing_requirements = five_ten_full_no_regression_ab,production_validated_selector,twenty_walltime_speedup"
        ),
        "task5_noop_guard": "has_task5_noop_no_regression_guard = true",
        "task10_noop_guard": "has_task10_noop_no_regression_guard = true",
        "task10_triggered_risk": (
            "has_task10_triggered_regression_evidence = true"
        ),
        "full_5_10_ab_missing": (
            "has_full_5_10_production_ab_evidence = false"
        ),
        "current_capture_target_coverage_event_count": (
            "current_capture_target_coverage_event_count = 114"
        ),
        "current_capture_target_exact_coverage_count": (
            "current_capture_target_exact_coverage_count = 3"
        ),
        "current_capture_target_uncovered_zero": (
            "current_capture_target_uncovered_count = 0"
        ),
        "current_capture_targets_all_covered": (
            "current_capture_targets_all_covered = true"
        ),
        "fixed_overhead": "固定开销极敏感",
        "trajectory_selector_not_generalized": (
            "trajectory selector 仍不能跨 context / instance / dataset 稳定泛化"
        ),
        "active_worker_closed": "Phase 8R 已正式关闭 active-worker 扩张子路线",
        "production_direction_false": "production_direction_proven = false",
        "robust_selector_false": "has_robust_all_fold_selector = false",
        "production_selector_false": "has_production_validated_selector = false",
        "walltime_speedup_false": "has_20_walltime_speedup_evidence = false",
        "goal_complete_false": "goal_complete = false",
        "calibration_only": "calibration_only_until_selector_passes = true",
        "selector_holdouts": (
            "required_selector_holdouts = context / instance / dataset"
        ),
        "addition_before_only": "selector_feature_scope = addition_before_only",
        "next_protocol_status": (
            "next_evidence_protocol_status = calibration_only_until_selector_passes"
        ),
        "next_protocol_catalog": "next_evidence_protocol_catalog = current",
        "current_stage_calibration_only": (
            "current_stage = calibration_only_selector_holdout"
        ),
        "next_protocol_gates": (
            "next_evidence_protocol_gates = exact_context_capture_and_replay_dataset,addition_before_selector,production_candidate_ab"
        ),
        "capture_ready_status": (
            "exact_context_capture_and_replay_dataset = ready_for_selector_calibration_attempt"
        ),
        "addition_before_status": (
            "addition_before_selector = calibrated_candidate_available"
        ),
        "production_ab_blocked": "production_candidate_ab = blocked",
        "selector_error_new_task_noop": (
            "false_positive_new_task_set_noop_count=21"
        ),
        "selector_error_new_task_improved": (
            "false_negative_new_task_set_improved_count=23"
        ),
        "selector_threshold_no_perfect": "perfect_threshold_count=0",
        "selector_threshold_zero_fp_recall": "0.267942583732",
        "selector_context_collision": "selector_context_collision=current",
        "selector_context_task_set_mixed": "task_set_mixed_group_count=6",
        "selector_context_sequence_mixed": "task_sequence_mixed_group_count=5",
        "selector_context_online_flags_mixed": "online_flags_mixed_row_count=278",
        "selector_local_feature_direction": (
            "selector_local_feature_direction=current"
        ),
        "selector_local_true_rc_flip": (
            "task_set_true_rc_direction_counts={improved_lower_mean:2,noop_lower_mean:4}"
        ),
        "selector_context_disambiguation": (
            "selector_context_disambiguation=current"
        ),
        "context_disambig_context_hash_zero": (
            "local_sequence_online_context_hash_mixed_group_count=0"
        ),
        "selector_context_scalar_candidates": (
            "selector_context_scalar_candidates=current"
        ),
        "control_objective_bin_zero": (
            "control_objective_bin_100_mixed_group_count=0"
        ),
        "selector_context_scalar_holdout": (
            "selector_context_scalar_holdout=current"
        ),
        "control_objective_holdout_zero": (
            "control_objective_holdout_passing_model_count=0"
        ),
        "selector_micro_vs_fold_gate": "selector_micro_vs_fold_gate=current",
        "micro_vs_fold_robust_zero": (
            "robust_all_fold_passing_feature_count=0"
        ),
        "selector_model_micro_vs_fold_gate": (
            "selector_model_micro_vs_fold_gate=current"
        ),
        "model_micro_vs_fold_robust_zero": (
            "robust_all_fold_passing_model_count=0"
        ),
        "selector_rule_family_search": "selector_rule_family_search=current",
        "rule_family_rule_count": "rule_family_rule_count=18887",
        "rule_family_material_zero": (
            "rule_family_material_all_fold_passing_rule_count=0"
        ),
        "selector_rule_family_search_20only": (
            "selector_rule_family_search_20only=current"
        ),
        "rule_family_20only_rule_count": (
            "rule_family_20only_rule_count=18901"
        ),
        "rule_family_20only_material_zero": (
            "rule_family_20only_material_all_fold_passing_rule_count=0"
        ),
        "selector_rule_family_train_holdout": (
            "selector_rule_family_train_holdout=current"
        ),
        "rule_family_train_context_folds": (
            "rule_family_train_context_material_passing_folds=17/28"
        ),
        "selector_rule_family_train_holdout_20only": (
            "selector_rule_family_train_holdout_20only=current"
        ),
        "rule_family_train_20only_context_folds": (
            "rule_family_train_20only_context_material_passing_folds=17/27"
        ),
        "selector_context_fold_anatomy": (
            "selector_context_fold_anatomy=current"
        ),
        "context_anatomy_false_positive_no_positive": (
            "context_fold_anatomy_twenty_false_positive_no_positive_context_count=4"
        ),
        "context_anatomy_missed_positive": (
            "context_fold_anatomy_twenty_missed_positive_context_count=3"
        ),
        "selector_context_feature_anatomy": (
            "selector_context_feature_anatomy=current"
        ),
        "context_feature_mixed_instance": (
            "context_feature_mixed_instance_group_count=2"
        ),
        "context_feature_mixed_dataset": (
            "context_feature_mixed_dataset_group_count=2"
        ),
        "production_selector_blocker_catalog": (
            "production_selector_blocker_catalog=current"
        ),
        "production_selector_blocker_status": (
            "production_selector_status=production_selector_not_validated"
        ),
        "production_selector_blocker_ids": (
            "production_selector_blocker_ids=concrete_false_positive_and_false_negative_examples,micro_average_gate_not_fold_stable,aggregate_model_gate_not_fold_stable,simple_rule_family_has_no_all_fold_rule,train_holdout_rules_not_context_stable,context_anatomy_has_opposite_failure_modes"
        ),
        "production_selector_blocker_checks": (
            "production_selector_blocker_all_checks_pass=true"
        ),
        "production_ab_entry_gate_catalog": (
            "production_ab_entry_gate_catalog=current"
        ),
        "production_ab_entry_status": (
            "production_candidate_ab_entry_status=blocked"
        ),
        "production_ab_entry_blockers": (
            "entry_gate_blockers=selector_not_validated,five_ten_full_no_regression_missing,twenty_speedup_missing"
        ),
        "production_ab_no_worker_default": (
            "must_not_enable_worker_default=true"
        ),
        "production_ab_no_certificate_gate": (
            "must_not_open_certificate_gate=true"
        ),
        "production_ab_selector_holdout_required": (
            "requires_selector_holdout_before_ab=true"
        ),
        "production_ab_forbidden_shortcuts": (
            "forbidden_shortcuts=post_addition_or_hindsight_features,single_context_replay_success,worker_negative_columns_without_walltime_roi,certificate_effect"
        ),
        "active_basis_capture_schema_feasibility": (
            "active_basis_capture_schema_feasibility=current"
        ),
        "active_basis_capture_all_fields_feasible": (
            "active_basis_capture_feasible_target_schema_field_count=9"
        ),
        "active_basis_capture_no_missing_fields": (
            "active_basis_capture_missing_target_schema_field_count=0"
        ),
        "active_basis_capture_no_certificate_effect": (
            "active_basis_capture_requires_certificate_effect=false"
        ),
        "active_basis_capture_supports_snapshot": (
            "active_basis_capture_supports_active_basis_snapshot=true"
        ),
        "active_basis_capture_implemented_default_off": (
            "active_basis_capture_schema_implementation_status=implemented_default_off"
        ),
        "robust_rule_selector_false": (
            "has_robust_all_fold_rule_selector = false"
        ),
        "robust_selector_available_false": (
            "robust_all_fold_selector_available=false"
        ),
        "code_boundary_audit": "code_boundary_audit=current",
        "code_boundary_capture_guarded": (
            "counterfactual_capture_guarded_by_config=true"
        ),
        "code_boundary_no_unvalidated_default": (
            "mainline_unvalidated_effect_default_enabled=false"
        ),
        "why_many_attempts_failed_current": "why_many_attempts_failed=current",
        "why_many_attempts_failed_status": (
            "why_many_attempts_failed_status=supported_but_optimization_direction_unproven"
        ),
        "why_many_attempts_failed_primary_causes": (
            "why_many_attempts_failed_primary_causes=small_scale_fixed_overhead_sensitivity,twenty_returned_batch_rmp_trajectory_coupling,addition_before_selector_not_production_validated"
        ),
        "why_many_attempts_failed_ruled_out_count": (
            "why_many_attempts_failed_ruled_out_hypothesis_count=5"
        ),
        "ledger_self_consistency_pass": "ledger_self_consistency_pass = true",
        "failure_matrix_current": "failure_matrix=current",
        "failure_matrix_route_count": "failure_matrix_route_count=7",
        "no_mainline_changes": "不应做主线求解逻辑大改",
        "no_certificate_gate": "不应打开 certificate gate",
    }
    phrase_presence = {
        key: phrase in current_section for key, phrase in required_phrases.items()
    }
    return {
        "source": str(path),
        "exists": path.exists(),
        "required_phrase_presence": phrase_presence,
        "check_goal_current_summary_is_current": bool(
            path.exists() and all(phrase_presence.values())
        ),
    }


def _goal_completion_blockers_report_metrics(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    required_phrases = {
        "objective_completion_audit": "objective_completion_audit = current",
        "root_cause_explanation_proved": (
            "root_cause_explanation_has_evidence = proved"
        ),
        "not_limited_to_pulse_proved": "not_limited_to_pulse = proved",
        "no_unvalidated_mainline_proved": (
            "no_unvalidated_mainline_change_before_proof = proved"
        ),
        "unproven_experiments_not_completion_proved": (
            "unproven_experiments_not_counted_as_completion = proved"
        ),
        "five_ten_noop_not_worker_success_proved": (
            "five_ten_no_regression_is_noop_guard_not_worker_success = proved"
        ),
        "stable_direction_not_proved": (
            "stable_production_optimization_direction = not_proved"
        ),
        "exact_5_10_20_not_proved": (
            "exact_5_10_no_regression_and_20_speedup = not_proved"
        ),
        "why_many_attempts_failed_current": "why_many_attempts_failed = current",
        "missing_requirements": (
            "missing_requirements = five_ten_full_no_regression_ab,production_validated_selector,twenty_walltime_speedup"
        ),
        "production_selector_false": "`production_validated_selector=false`",
        "production_ab_blocked": "production A/B entry gate 仍 blocked",
        "goal_active": "因此目标必须保持 active",
    }
    stale_phrases = {
        "goal_complete_true": "goal_complete = true",
        "mark_complete": "completion_decision = mark_goal_complete",
        "production_direction_proved": (
            "stable_production_optimization_direction = proved"
        ),
        "exact_5_10_20_proved": (
            "exact_5_10_no_regression_and_20_speedup = proved"
        ),
    }
    phrase_presence = {
        key: phrase in text for key, phrase in required_phrases.items()
    }
    stale_presence = {key: phrase in text for key, phrase in stale_phrases.items()}
    return {
        "source": str(path),
        "exists": path.exists(),
        "required_phrase_presence": phrase_presence,
        "stale_phrase_presence": stale_presence,
        "check_goal_completion_blockers_report_is_current": bool(
            path.exists()
            and all(phrase_presence.values())
            and not any(stale_presence.values())
        ),
    }


def _objective_completion_audit_catalog_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    expected_proved = [
        "root_cause_explanation_has_evidence",
        "not_limited_to_pulse",
        "no_unvalidated_mainline_change_before_proof",
        "unproven_experiments_not_counted_as_completion",
        "five_ten_no_regression_is_noop_guard_not_worker_success",
    ]
    expected_not_proved = [
        "stable_production_optimization_direction",
        "exact_5_10_no_regression_and_20_speedup",
    ]
    expected_missing = [
        "five_ten_full_no_regression_ab",
        "production_validated_selector",
        "twenty_walltime_speedup",
    ]
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "catalog_current": "objective_completion_audit_catalog = current"
        in report_text,
        "goal_complete_false": "goal_complete = false" in report_text,
        "should_mark_false": "should_mark_goal_complete = false" in report_text,
        "decision_keep_active": "completion_decision = keep_goal_active"
        in report_text,
        "missing": (
            "missing_requirements = five_ten_full_no_regression_ab,production_validated_selector,twenty_walltime_speedup"
            in report_text
        ),
        "stable_direction_not_proved": (
            "stable_production_optimization_direction = not_proved"
            in report_text
        ),
        "exact_5_10_20_not_proved": (
            "exact_5_10_no_regression_and_20_speedup = not_proved"
            in report_text
        ),
        "no_worker_default": "must_not_enable_worker_default = true"
        in report_text,
        "no_certificate_gate": "must_not_open_certificate_gate = true"
        in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "goal_complete": summary.get("goal_complete"),
        "completion_decision": summary.get("completion_decision"),
        "proved_requirements": summary.get("proved_requirements"),
        "not_proved_requirements": summary.get("not_proved_requirements"),
        "missing_requirements": summary.get("missing_requirements"),
        "report_phrase_presence": report_phrases,
        "check_objective_completion_audit_catalog_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("goal_complete") is False
            and summary.get("should_mark_goal_complete") is False
            and summary.get("completion_decision") == "keep_goal_active"
            and summary.get("proved_requirements") == expected_proved
            and summary.get("not_proved_requirements") == expected_not_proved
            and summary.get("missing_requirements") == expected_missing
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _next_evidence_protocol_catalog_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    expected_gate_order = [
        "exact_context_capture_and_replay_dataset",
        "addition_before_selector",
        "production_candidate_ab",
    ]
    expected_readiness = {
        "exact_context_capture_and_replay_dataset": True,
        "addition_before_selector": True,
        "production_candidate_ab": False,
    }
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "catalog_current": "next_evidence_protocol_catalog = current"
        in report_text,
        "status": (
            "next_evidence_protocol_status = calibration_only_until_selector_passes"
            in report_text
        ),
        "stage": "current_stage = calibration_only_selector_holdout" in report_text,
        "gate_order": (
            "gate_order = exact_context_capture_and_replay_dataset,addition_before_selector,production_candidate_ab"
            in report_text
        ),
        "production_ab_not_passed": "production_candidate_ab_passed = false"
        in report_text,
        "addition_before_selector_status": (
            "addition_before_selector_status = calibrated_candidate_available_not_production_validated"
            in report_text
        ),
        "production_selector_not_validated": (
            "production_selector_validated = false" in report_text
        ),
        "production_ab_blocked": (
            "production_candidate_ab_status = blocked_until_production_selector_and_20_speedup_pass"
            in report_text
        ),
        "feature_scope": "selector_feature_scope = addition_before_only"
        in report_text,
        "holdouts": "required_selector_holdouts = context/instance/dataset"
        in report_text,
        "forbidden_shortcuts": (
            "forbidden_shortcuts = post_addition_or_hindsight_features,single_context_replay_success,worker_negative_columns_without_walltime_roi,certificate_effect"
            in report_text
        ),
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "status": summary.get("status"),
        "current_stage": summary.get("current_stage"),
        "gate_order": summary.get("gate_order"),
        "readiness_status": summary.get("readiness_status"),
        "production_candidate_ab_status": summary.get(
            "production_candidate_ab_status"
        ),
        "addition_before_selector_status": summary.get(
            "addition_before_selector_status"
        ),
        "production_selector_validated": summary.get("production_selector_validated"),
        "report_phrase_presence": report_phrases,
        "check_next_evidence_protocol_catalog_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("status") == "calibration_only_until_selector_passes"
            and summary.get("current_stage") == "calibration_only_selector_holdout"
            and summary.get("gate_order") == expected_gate_order
            and summary.get("readiness_status") == expected_readiness
            and summary.get("selector_feature_scope") == "addition_before_only"
            and summary.get("required_selector_holdouts")
            == ["context", "instance", "dataset"]
            and summary.get("production_candidate_ab_status")
            == "blocked_until_production_selector_and_20_speedup_pass"
            and summary.get("addition_before_selector_status")
            == "calibrated_candidate_available_not_production_validated"
            and summary.get("production_selector_validated") is False
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _evidence_bundle_manifest_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    expected_conclusions = [
        "small_scale_fixed_overhead_sensitivity",
        "twenty_negative_columns_not_sufficient",
        "true_rc_negative_can_be_high_impact_or_noop",
        "selector_not_production_validated",
        "exact_context_capture_ready_but_calibration_only",
        "objective_completion_blocked",
    ]
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "manifest_current": "root_cause_evidence_bundle_manifest = current"
        in report_text,
        "goal_complete_false": "goal_complete = false" in report_text,
        "keep_active": "completion_decision = keep_goal_active" in report_text,
        "entry_count": "evidence_bundle_entry_count = 6" in report_text,
        "missing_zero": "missing_artifact_count = 0" in report_text,
        "refresh_command": "BPC_future/scripts/verify_root_cause_evidence.py"
        in report_text,
        "rebuild_command": "BPC_future/scripts/rebuild_root_cause_evidence_bundle.py"
        in report_text,
        "objective_blocked": "objective_completion_blocked" in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "goal_complete": summary.get("goal_complete"),
        "completion_decision": summary.get("completion_decision"),
        "entry_count": summary.get("entry_count"),
        "primary_artifact_count": summary.get("primary_artifact_count"),
        "missing_artifacts": summary.get("missing_artifacts"),
        "bundle_rebuild_script": summary.get("bundle_rebuild_script"),
        "bundle_rebuild_script_exists": summary.get("bundle_rebuild_script_exists"),
        "conclusion_ids": summary.get("conclusion_ids"),
        "report_phrase_presence": report_phrases,
        "check_evidence_bundle_manifest_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("goal_complete") is False
            and summary.get("completion_decision") == "keep_goal_active"
            and summary.get("entry_count") == 6
            and int(summary.get("primary_artifact_count", 0)) >= 50
            and summary.get("missing_artifacts") == []
            and summary.get("bundle_rebuild_script")
            == str(EVIDENCE_BUNDLE_REBUILD_SCRIPT)
            and summary.get("bundle_rebuild_script_exists") is True
            and EVIDENCE_BUNDLE_REBUILD_SCRIPT.exists()
            and summary.get("conclusion_ids") == expected_conclusions
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _evidence_bundle_rebuild_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "rebuild_current": "root_cause_evidence_rebuild = current" in report_text,
        "diagnostic_only": "diagnostic_only = true" in report_text,
        "no_bpc_pricing": "runs_bpc_or_pricing = false" in report_text,
        "all_commands_pass": "all_commands_pass = true" in report_text,
        "final_ledger_pass": "final_ledger_all_checks_pass = true" in report_text,
        "final_goal_false": "final_goal_complete = false" in report_text,
        "keep_active": "final_completion_decision = keep_goal_active" in report_text,
    }
    failed_commands = [
        item
        for item in summary.get("commands", [])
        if int(item.get("returncode", 1)) != 0
    ]
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "diagnostic_only": summary.get("diagnostic_only"),
        "runs_bpc_or_pricing": summary.get("runs_bpc_or_pricing"),
        "command_count": summary.get("command_count"),
        "failed_command_count": len(failed_commands),
        "final_ledger_all_checks_pass": summary.get("final_ledger_all_checks_pass"),
        "final_goal_complete": summary.get("final_goal_complete"),
        "final_completion_decision": summary.get("final_completion_decision"),
        "report_phrase_presence": report_phrases,
        "check_evidence_rebuild_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("diagnostic_only") is True
            and summary.get("runs_bpc_or_pricing") is False
            and int(summary.get("command_count", 0)) >= 10
            and not failed_commands
            and summary.get("final_ledger_all_checks_pass") is True
            and summary.get("final_goal_complete") is False
            and summary.get("final_completion_decision") == "keep_goal_active"
            and all(report_phrases.values())
        ),
    }


def _exact_context_capture_status_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    status = summary.get("status", {})
    replay_dataset = summary.get("replay_dataset", {})
    selector_state = summary.get("selector_state", {})
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "ready_for_selector_calibration": (
            "ready_for_selector_calibration_attempt" in report_text
        ),
        "not_production": "它不能证明" in report_text,
        "holdout_gate": "required_selector_holdouts = context / instance / dataset"
        in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "status": status,
        "ready_case_count": _as_int(replay_dataset.get("ready_case_count")),
        "candidate_row_count": _as_int(replay_dataset.get("candidate_row_count")),
        "high_impact_candidate_count": _as_int(
            replay_dataset.get("high_impact_candidate_count")
        ),
        "noop_candidate_count": _as_int(replay_dataset.get("noop_candidate_count")),
        "production_validated_selector": selector_state.get(
            "production_validated_selector"
        ),
        "report_phrase_presence": report_phrases,
        "check_exact_context_capture_ready_for_calibration_only": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and status.get("exact_context_capture_and_replay_dataset")
            == "ready_for_selector_calibration_attempt"
            and status.get("production_candidate_ab")
            == "blocked_until_selector_holdout_and_20_speedup"
            and _as_int(replay_dataset.get("ready_case_count")) > 0
            and _as_int(replay_dataset.get("high_impact_candidate_count")) > 0
            and _as_int(replay_dataset.get("noop_candidate_count")) > 0
            and selector_state.get("production_validated_selector") is False
            and all(report_phrases.values())
            and all(checks.values())
        ),
    }


def _root_cause_code_boundary_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    derived = summary.get("derived", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "code_boundary_title": "Root Cause Code Boundary" in report_text,
        "guarded_capture": "counterfactual_capture_guarded_by_config = true"
        in report_text,
        "diagnostic_only": "counterfactual_capture_diagnostic_only = true"
        in report_text,
        "no_official_effect": "counterfactual_capture_official_bound_effect = false"
        in report_text,
        "profile_defaults": "profile_priority_defaults_empty = true" in report_text,
        "no_unvalidated_default": (
            "mainline_unvalidated_effect_default_enabled = false" in report_text
        ),
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "checks": checks,
        "derived": derived,
        "counterfactual_capture_guarded_by_config": bool(
            checks.get("counterfactual_capture_guarded_by_config")
        ),
        "counterfactual_capture_diagnostic_only": bool(
            derived.get("counterfactual_capture_diagnostic_only")
        ),
        "counterfactual_capture_default_enabled": bool(
            derived.get("counterfactual_capture_default_enabled")
        ),
        "counterfactual_capture_certificate_capable": bool(
            derived.get("counterfactual_capture_certificate_capable")
        ),
        "counterfactual_capture_official_bound_effect": bool(
            derived.get("counterfactual_capture_official_bound_effect")
        ),
        "profile_priority_defaults_empty": bool(
            derived.get("profile_priority_defaults_empty")
        ),
        "experimental_profiles_not_default": bool(
            derived.get("experimental_profiles_not_default")
        ),
        "mainline_unvalidated_effect_default_enabled": bool(
            derived.get("mainline_unvalidated_effect_default_enabled")
        ),
        "report_phrase_presence": report_phrases,
        "check_code_boundary_no_unvalidated_production_effect": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and checks.get("counterfactual_capture_guarded_by_config") is True
            and derived.get("counterfactual_capture_diagnostic_only") is True
            and derived.get("counterfactual_capture_default_enabled") is False
            and derived.get("counterfactual_capture_certificate_capable") is False
            and derived.get("counterfactual_capture_official_bound_effect") is False
            and derived.get("profile_priority_defaults_empty") is True
            and derived.get("experimental_profiles_not_default") is True
            and derived.get("mainline_unvalidated_effect_default_enabled") is False
            and all(report_phrases.values())
        ),
    }


def _root_cause_failure_matrix_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    routes = list(summary.get("routes", []))
    routes_by_id = {
        str(route.get("route_id", "")): route
        for route in routes
        if route.get("route_id")
    }
    required_route_ids = {
        "pulse_wiring_or_certificate_semantics",
        "more_true_rc_negative_columns",
        "expand_worker_budget_or_default_worker",
        "true_rc_threshold_or_local_column_selector",
        "simple_ml_or_batch_selector",
        "simple_rmp_trajectory_proxy_selector",
        "single_context_or_local_replay_success",
    }
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "title": "Root Cause Failure Matrix" in report_text,
        "route_count": "route_count = 7" in report_text,
        "production_false": "production_direction_proven = false" in report_text,
        "missing_requirements": (
            "missing_requirement_names = five_ten_full_no_regression_ab,production_validated_selector,twenty_walltime_speedup"
            in report_text
        ),
        "worker_budget": "继续扩大 worker / audit / probe 会伤害 5/10"
        in report_text,
        "more_negative_not_enough": (
            "继续找更多 true-RC negative columns 不能自动改善 20"
            in report_text
        ),
        "selector_holdout": "context / instance / dataset holdout" in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "route_count": len(routes),
        "required_route_ids": sorted(required_route_ids),
        "actual_route_ids": sorted(routes_by_id),
        "missing_route_ids": sorted(required_route_ids - set(routes_by_id)),
        "route_statuses": {
            route_id: routes_by_id.get(route_id, {}).get("status")
            for route_id in sorted(required_route_ids)
        },
        "route_all_checks": {
            route_id: bool(routes_by_id.get(route_id, {}).get("all_route_checks_pass"))
            for route_id in sorted(required_route_ids)
        },
        "production_direction_proven": bool(
            summary.get("summary", {}).get("production_direction_proven")
        ),
        "missing_requirement_names": list(
            summary.get("summary", {}).get("missing_requirement_names", [])
        ),
        "report_phrase_presence": report_phrases,
        "check_failure_matrix_routes_have_evidence": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and set(routes_by_id) >= required_route_ids
            and len(routes) == 7
            and all(
                bool(routes_by_id[route_id].get("all_route_checks_pass"))
                for route_id in required_route_ids
            )
            and summary.get("summary", {}).get("production_direction_proven")
            is False
            and summary.get("summary", {}).get("missing_requirement_names")
            == [
                "five_ten_full_no_regression_ab",
                "production_validated_selector",
                "twenty_walltime_speedup",
            ]
            and all(report_phrases.values())
        ),
    }
def _selector_holdout_status_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    exact = summary.get("exact_replay_selector", {})
    broad = summary.get("broad_candidate_selector", {})
    blockers = summary.get("column_local_selector_blockers", {})
    selected20 = summary.get("selected20_repeat_ab", {})
    status = summary.get("status", {})
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "not_production_validated": "selector_holdout = not_production_validated"
        in report_text,
        "false_positive_count": "false_positive_count = 22" in report_text,
        "false_negative_count": "false_negative_count = 31" in report_text,
        "selected20_status": "profile_statuses = ['TIME_LIMIT']" in report_text,
        "context_collision": "task_set_mixed_group_count = 6" in report_text,
        "local_direction": "task_set_true_rc_direction_counts = {'improved_lower_mean': 2, 'noop_lower_mean': 4}"
        in report_text,
        "column_local_blocker": "列局部形态或简单单调 true-RC/cost 规则"
        in report_text,
        "next_gate": "context / instance / dataset holdout" in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "status": status,
        "exact_row_count": _as_int(exact.get("row_count")),
        "exact_false_positive_count": _as_int(exact.get("false_positive_count")),
        "exact_false_negative_count": _as_int(exact.get("false_negative_count")),
        "broad_dataset_holdout_pass_count": _as_int(
            broad.get("dataset_holdout_pass_count")
        ),
        "broad_instance_holdout_pass_count": _as_int(
            broad.get("instance_holdout_pass_count")
        ),
        "task_set_mixed_group_count": _as_int(
            blockers.get("task_set_mixed_group_count")
        ),
        "task_sequence_mixed_group_count": _as_int(
            blockers.get("task_sequence_mixed_group_count")
        ),
        "online_flags_mixed_row_count": _as_int(
            blockers.get("online_flags_mixed_row_count")
        ),
        "task_set_true_rc_improved_lower_count": _as_int(
            (blockers.get("task_set_true_rc_direction_counts") or {}).get(
                "improved_lower_mean"
            )
        ),
        "task_set_true_rc_noop_lower_count": _as_int(
            (blockers.get("task_set_true_rc_direction_counts") or {}).get(
                "noop_lower_mean"
            )
        ),
        "selected20_profile_row_count": _as_int(
            selected20.get("profile_row_count")
        ),
        "selected20_primal_deltas": selected20.get("primal_deltas_vs_baseline", []),
        "report_phrase_presence": report_phrases,
        "check_selector_holdout_not_production_validated": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and status.get("selector_holdout") == "not_production_validated"
            and status.get("production_candidate_ab") == "blocked"
            and _as_int(exact.get("row_count")) >= 280
            and _as_int(exact.get("false_positive_count")) > 0
            and _as_int(exact.get("false_negative_count")) > 0
            and _as_int(broad.get("dataset_holdout_pass_count")) == 0
            and _as_int(broad.get("instance_holdout_pass_count")) == 0
            and _as_int(blockers.get("task_set_mixed_group_count")) == 6
            and _as_int(blockers.get("task_sequence_mixed_group_count")) == 5
            and _as_int(blockers.get("online_flags_mixed_row_count")) == 278
            and _as_int(
                (blockers.get("task_set_true_rc_direction_counts") or {}).get(
                    "improved_lower_mean"
                )
            )
            == 2
            and _as_int(
                (blockers.get("task_set_true_rc_direction_counts") or {}).get(
                    "noop_lower_mean"
                )
            )
            == 4
            and selected20.get("profile_statuses") == ["TIME_LIMIT"]
            and all(report_phrases.values())
            and all(checks.values())
        ),
    }


def _selector_error_anatomy_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    anatomy = summary.get("anatomy", {})
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "false_positive_count": "false_positive_count = 22" in report_text,
        "false_negative_count": "false_negative_count = 31" in report_text,
        "new_task_set_noop": "false_positive_new_task_set_noop_count = 21"
        in report_text,
        "new_task_set_improved": "false_negative_new_task_set_improved_count = 23"
        in report_text,
        "not_production": "不能作为 production selector" in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "recommended_selector_candidate": summary.get(
            "recommended_selector_candidate"
        ),
        "row_count": _as_int(anatomy.get("row_count")),
        "false_positive_count": _as_int(anatomy.get("false_positive_count")),
        "false_negative_count": _as_int(anatomy.get("false_negative_count")),
        "false_positive_new_task_set_noop_count": _as_int(
            anatomy.get("false_positive_new_task_set_noop_count")
        ),
        "false_negative_new_task_set_improved_count": _as_int(
            anatomy.get("false_negative_new_task_set_improved_count")
        ),
        "report_phrase_presence": report_phrases,
        "check_selector_error_anatomy_blocks_simple_selector": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and _as_int(anatomy.get("row_count")) == 280
            and _as_int(anatomy.get("false_positive_count")) == 22
            and _as_int(anatomy.get("false_negative_count")) == 31
            and _as_int(anatomy.get("false_positive_new_task_set_noop_count"))
            > 0
            and _as_int(anatomy.get("false_negative_new_task_set_improved_count"))
            > 0
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _selector_counterexample_catalog_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    key_counterexamples = summary.get("key_counterexamples", {})
    report_phrases = {
        "catalog_current": "selector_counterexample_catalog = current" in report_text,
        "fp_count": "false_positive_count = 22" in report_text,
        "fn_count": "false_negative_count = 31" in report_text,
        "new_task_set_noop_example": (
            "new-task-set 但 replay no-op 的 false positive" in report_text
        ),
        "weak_rc_improved_example": (
            "true-RC 较弱但 replay improved 的 false negative" in report_text
        ),
        "not_production": "production_validated_selector = false" in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "recommended_selector_candidate": summary.get(
            "recommended_selector_candidate"
        ),
        "false_positive_count": _as_int(summary.get("false_positive_count")),
        "false_negative_count": _as_int(summary.get("false_negative_count")),
        "false_positive_new_task_set_noop_count": _as_int(
            summary.get("false_positive_new_task_set_noop_count")
        ),
        "false_negative_new_task_set_improved_count": _as_int(
            summary.get("false_negative_new_task_set_improved_count")
        ),
        "has_new_task_set_noop_false_positive": bool(
            key_counterexamples.get("new_task_set_noop_false_positive")
        ),
        "has_new_task_set_improved_false_negative": bool(
            key_counterexamples.get("new_task_set_improved_false_negative")
        ),
        "report_phrase_presence": report_phrases,
        "check_selector_counterexamples_block_production_selector": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and _as_int(summary.get("false_positive_count")) == 22
            and _as_int(summary.get("false_negative_count")) == 31
            and _as_int(summary.get("false_positive_new_task_set_noop_count"))
            == 21
            and _as_int(summary.get("false_negative_new_task_set_improved_count"))
            == 23
            and bool(key_counterexamples.get("new_task_set_noop_false_positive"))
            and bool(key_counterexamples.get("new_task_set_improved_false_negative"))
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _production_selector_blocker_catalog_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    blocker_ids = [str(item.get("blocker_id", "")) for item in summary.get("blockers", [])]
    expected_blockers = [
        "concrete_false_positive_and_false_negative_examples",
        "micro_average_gate_not_fold_stable",
        "aggregate_model_gate_not_fold_stable",
        "simple_rule_family_has_no_all_fold_rule",
        "train_holdout_rules_not_context_stable",
        "context_anatomy_has_opposite_failure_modes",
    ]
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "catalog_current": "production_selector_blocker_catalog = current"
        in report_text,
        "status": "production_selector_status = production_selector_not_validated"
        in report_text,
        "feature_scope": "selector_feature_scope = addition_before_only"
        in report_text,
        "holdouts": "required_selector_holdouts = context / instance / dataset"
        in report_text,
        "no_robust_feature": "robust_all_fold_passing_features = []"
        in report_text,
        "no_robust_model": "robust_all_fold_passing_models = []" in report_text,
        "no_rule": "material_all_fold_passing_rule_count = 0" in report_text,
        "train_context_folds": (
            "rule_family_train_context_material_passing_folds = 17/28"
            in report_text
        ),
        "still_blocked": "production_candidate_ab = blocked" in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "status": summary.get("status"),
        "feature_scope": summary.get("feature_scope"),
        "required_holdouts": summary.get("required_holdouts"),
        "blocker_ids": blocker_ids,
        "report_phrase_presence": report_phrases,
        "check_production_selector_blockers_are_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("status") == "production_selector_not_validated"
            and summary.get("feature_scope") == "addition_before_only"
            and summary.get("required_holdouts") == ["context", "instance", "dataset"]
            and blocker_ids == expected_blockers
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _selector_failure_mechanism_audit_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    mechanism_ids = [
        str(item.get("mechanism_id", ""))
        for item in summary.get("mechanisms", [])
    ]
    expected_mechanisms = [
        "opposite_context_failure_modes",
        "local_column_shape_insufficient",
        "instance_and_dataset_do_not_explain_context",
        "micro_average_hides_fold_failures",
        "simple_context_scalars_not_enough",
        "train_holdout_rule_family_not_stable",
    ]
    required_test_ids = [
        str(item.get("test_id", ""))
        for item in summary.get("required_next_tests", [])
    ]
    expected_tests = [
        "addition_before_only_feature_scope",
        "context_instance_dataset_holdout",
        "opposite_failure_mode_coverage",
        "exact_context_replay_no_certificate_effect",
        "production_bpc_ab_after_selector",
    ]
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "audit_current": "selector_failure_mechanism_audit = current"
        in report_text,
        "mechanism_count": "mechanism_count = 6" in report_text,
        "not_validated": (
            "current_production_selector_status = not_validated" in report_text
        ),
        "calibration_only": (
            "current_allowed_work = calibration_only_selector_holdout"
            in report_text
        ),
        "opposite_modes": "opposite_context_failure_modes" in report_text,
        "local_shape": "local_column_shape_insufficient" in report_text,
        "next_tests": "addition_before_only_feature_scope" in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "mechanism_count": _as_int(summary.get("mechanism_count")),
        "mechanism_ids": mechanism_ids,
        "required_next_test_ids": required_test_ids,
        "current_production_selector_status": summary.get(
            "current_production_selector_status"
        ),
        "current_allowed_work": summary.get("current_allowed_work"),
        "report_phrase_presence": report_phrases,
        "check_selector_failure_mechanism_audit_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and _as_int(summary.get("mechanism_count")) == 6
            and mechanism_ids == expected_mechanisms
            and required_test_ids == expected_tests
            and summary.get("current_production_selector_status")
            == "not_validated"
            and summary.get("current_allowed_work")
            == "calibration_only_selector_holdout"
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _selector_context_feature_gap_audit_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    proxy_ids = [
        str(item.get("proxy_id", ""))
        for item in summary.get("proxy_results", [])
    ]
    expected_proxy_ids = [
        "local_sequence",
        "online_flags_and_cg_iter",
        "instance_identity",
        "dataset_identity",
        "exact_context_hash",
        "control_objective_bin_100",
        "threshold_context_scalar",
    ]
    required_property_ids = [
        str(item.get("property_id", ""))
        for item in summary.get("required_feature_properties", [])
    ]
    expected_property_ids = [
        "addition_before_observable",
        "rmp_trajectory_context",
        "less_specific_than_hash",
        "stronger_than_scalar_context",
        "holdout_stable",
    ]
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "audit_current": "selector_context_feature_gap_audit = current"
        in report_text,
        "proxy_count": "proxy_count = 7" in report_text,
        "status": (
            "current_status = feature_gap_identified_not_production_selector"
            in report_text
        ),
        "allowed_work": (
            "current_allowed_work = calibration_only_feature_design_and_holdout"
            in report_text
        ),
        "local_sequence": "local_sequence" in report_text,
        "context_hash": "exact_context_hash" in report_text,
        "control_objective": "control_objective_bin_100" in report_text,
        "rmp_context": "rmp_trajectory_context" in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "proxy_count": _as_int(summary.get("proxy_count")),
        "proxy_ids": proxy_ids,
        "required_property_ids": required_property_ids,
        "current_status": summary.get("current_status"),
        "current_allowed_work": summary.get("current_allowed_work"),
        "report_phrase_presence": report_phrases,
        "check_selector_context_feature_gap_audit_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and _as_int(summary.get("proxy_count")) == 7
            and proxy_ids == expected_proxy_ids
            and required_property_ids == expected_property_ids
            and summary.get("current_status")
            == "feature_gap_identified_not_production_selector"
            and summary.get("current_allowed_work")
            == "calibration_only_feature_design_and_holdout"
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _selector_feature_availability_audit_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "audit_current": "selector_feature_availability_audit = current"
        in report_text,
        "row_count": "row_count = 280" in report_text,
        "addition_before": "addition_before_present_count = 16" in report_text,
        "post_addition": "post_addition_label_present_count = 6" in report_text,
        "desired_present": "desired_rmp_trajectory_present_count = 17"
        in report_text,
        "desired_missing": "desired_rmp_trajectory_missing_count = 0"
        in report_text,
        "present_fields": "dual_l1_norm_before" in report_text,
        "snapshot_fields": "rmp_degeneracy_pressure_before" in report_text,
        "interpretation": "active-basis churn" in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "dataset_count": _as_int(summary.get("dataset_count")),
        "row_count": _as_int(summary.get("row_count")),
        "addition_before_present_count": len(
            summary.get("addition_before_present", [])
        ),
        "post_addition_label_present_count": len(
            summary.get("post_addition_label_present", [])
        ),
        "desired_rmp_trajectory_present_count": len(
            summary.get("desired_rmp_trajectory_present", [])
        ),
        "desired_rmp_trajectory_missing_count": len(
            summary.get("desired_rmp_trajectory_missing", [])
        ),
        "desired_rmp_trajectory_missing": summary.get(
            "desired_rmp_trajectory_missing", []
        ),
        "report_phrase_presence": report_phrases,
        "check_selector_feature_availability_audit_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and _as_int(summary.get("dataset_count")) == 5
            and _as_int(summary.get("row_count")) == 280
            and len(summary.get("addition_before_present", [])) == 16
            and len(summary.get("post_addition_label_present", [])) == 6
            and len(summary.get("desired_rmp_trajectory_present", [])) == 17
            and len(summary.get("desired_rmp_trajectory_missing", [])) == 0
            and "active_hash_before"
            in summary.get("desired_rmp_trajectory_present", [])
            and "dual_hash_before"
            in summary.get("desired_rmp_trajectory_present", [])
            and "column_pool_size_before"
            in summary.get("desired_rmp_trajectory_present", [])
            and "lambda_active_count_before"
            in summary.get("desired_rmp_trajectory_present", [])
            and "active_basis_churn_count_before"
            in summary.get("desired_rmp_trajectory_present", [])
            and "rmp_degeneracy_pressure_before"
            in summary.get("desired_rmp_trajectory_present", [])
            and "recent_objective_delta_before"
            in summary.get("desired_rmp_trajectory_present", [])
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _production_ab_entry_gate_catalog_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    blockers = [str(item) for item in summary.get("entry_gate_blockers", [])]
    expected_blockers = [
        "selector_not_validated",
        "five_ten_full_no_regression_missing",
        "twenty_speedup_missing",
    ]
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "catalog_current": "production_ab_entry_gate_catalog = current"
        in report_text,
        "status_blocked": (
            "production_candidate_ab_entry_status = blocked" in report_text
        ),
        "production_ab_blocked": "production_candidate_ab = blocked"
        in report_text,
        "blockers": (
            "entry_gate_blockers = selector_not_validated,five_ten_full_no_regression_missing,twenty_speedup_missing"
            in report_text
        ),
        "no_worker_default": "must_not_enable_worker_default = true"
        in report_text,
        "no_certificate_gate": "must_not_open_certificate_gate = true"
        in report_text,
        "selector_holdout_required": (
            "requires_selector_holdout_before_ab = true" in report_text
        ),
        "five_ten_required": (
            "requires_5_10_full_no_regression_before_ab = true"
            in report_text
        ),
        "twenty_required": (
            "requires_selected_20_speedup_before_ab = true" in report_text
        ),
        "feature_scope": "selector_feature_scope = addition_before_only"
        in report_text,
        "required_holdouts": "required_selector_holdouts = context/instance/dataset"
        in report_text,
        "forbidden_shortcuts": (
            "forbidden_shortcuts = post_addition_or_hindsight_features,single_context_replay_success,worker_negative_columns_without_walltime_roi,certificate_effect"
            in report_text
        ),
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "status": summary.get("production_candidate_ab_entry_status"),
        "entry_gate_blockers": blockers,
        "must_not_enable_worker_default": summary.get(
            "must_not_enable_worker_default"
        ),
        "must_not_open_certificate_gate": summary.get(
            "must_not_open_certificate_gate"
        ),
        "requires_selector_holdout_before_ab": summary.get(
            "requires_selector_holdout_before_ab"
        ),
        "selector_feature_scope": summary.get("selector_feature_scope"),
        "required_selector_holdouts": summary.get("required_selector_holdouts"),
        "forbidden_shortcuts": summary.get("forbidden_shortcuts"),
        "report_phrase_presence": report_phrases,
        "check_production_ab_entry_gate_is_blocked": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("production_candidate_ab_entry_status") == "blocked"
            and summary.get("production_candidate_ab") == "blocked"
            and blockers == expected_blockers
            and summary.get("must_not_enable_worker_default") is True
            and summary.get("must_not_open_certificate_gate") is True
            and summary.get("requires_selector_holdout_before_ab") is True
            and summary.get("requires_5_10_full_no_regression_before_ab") is True
            and summary.get("requires_selected_20_speedup_before_ab") is True
            and summary.get("selector_feature_scope") == "addition_before_only"
            and summary.get("required_selector_holdouts")
            == ["context", "instance", "dataset"]
            and summary.get("forbidden_shortcuts")
            == [
                "post_addition_or_hindsight_features",
                "single_context_replay_success",
                "worker_negative_columns_without_walltime_roi",
                "certificate_effect",
            ]
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _capture_schema_feasibility_audit_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    field_status_counts = summary.get("field_status_counts", {})
    manifest_field_counts = summary.get("manifest_field_counts", {})
    report_phrases = {
        "audit_current": "capture_schema_feasibility_audit = current"
        in report_text,
        "candidate_rows": "candidate_row_count = 280" in report_text,
        "manifest_cases": "manifest_case_count = 82" in report_text,
        "present_fields": "desired_present_in_candidate_rows_count = 17"
        in report_text,
        "missing_fields": "desired_missing_in_candidate_rows_count = 0"
        in report_text,
        "metric_definition": "requires_metric_definition_count = 0"
        in report_text,
        "snapshot_metric": "active_basis_snapshot_metric_field_count = 2"
        in report_text,
        "history_recovered": "recovered_from_event_history_field_count = 8"
        in report_text,
        "production_blocked": "不能进入 production A/B" in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "candidate_row_count": _as_int(summary.get("candidate_row_count")),
        "manifest_case_count": _as_int(summary.get("manifest_case_count")),
        "desired_missing_in_candidate_rows_count": len(
            summary.get("desired_missing_in_candidate_rows", [])
        ),
        "field_status_counts": field_status_counts,
        "direct_or_alias_available_field_count": _as_int(
            summary.get("direct_or_alias_available_field_count")
        ),
        "derivable_from_manifest_field_count": _as_int(
            summary.get("derivable_from_manifest_field_count")
        ),
        "recovered_from_event_history_field_count": _as_int(
            summary.get("recovered_from_event_history_field_count")
        ),
        "requires_metric_definition_count": _as_int(
            summary.get("requires_metric_definition_count")
        ),
        "requires_manifest_pass_through_count": _as_int(
            summary.get("requires_manifest_pass_through_count")
        ),
        "requires_event_history_join_count": _as_int(
            summary.get("requires_event_history_join_count")
        ),
        "requires_capture_schema_extension_count": _as_int(
            summary.get("requires_capture_schema_extension_count")
        ),
        "manifest_field_counts": manifest_field_counts,
        "complete_pool_case_count": _as_int(summary.get("complete_pool_case_count")),
        "recommended_next_action": summary.get("recommended_next_action", ""),
        "report_phrase_presence": report_phrases,
        "check_capture_schema_feasibility_audit_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("diagnostic_only") is True
            and summary.get("runs_bpc_or_pricing") is False
            and _as_int(summary.get("candidate_row_count")) == 280
            and _as_int(summary.get("manifest_case_count")) == 82
            and len(summary.get("desired_present_in_candidate_rows", [])) == 17
            and len(summary.get("desired_missing_in_candidate_rows", [])) == 0
            and _as_int(summary.get("direct_or_alias_available_field_count")) == 3
            and _as_int(summary.get("derivable_from_manifest_field_count")) == 4
            and _as_int(summary.get("recovered_from_event_history_field_count")) == 8
            and _as_int(summary.get("active_basis_snapshot_metric_field_count")) == 2
            and _as_int(summary.get("requires_metric_definition_count")) == 0
            and _as_int(summary.get("requires_manifest_pass_through_count")) == 0
            and _as_int(summary.get("requires_event_history_join_count")) == 0
            and _as_int(summary.get("requires_capture_schema_extension_count")) == 0
            and _as_int(summary.get("complete_pool_case_count")) == 82
            and manifest_field_counts.get("true_dual_hash") == 82
            and manifest_field_counts.get("true_dual_vector") == 82
            and manifest_field_counts.get("pool_journeys") == 82
            and manifest_field_counts.get("active_hash_before") == 80
            and checks.get("candidate_rows_include_recoverable_manifest_fields")
            is True
            and checks.get("candidate_rows_still_missing_schema_and_history_fields")
            is True
            and checks.get("active_basis_snapshot_metric_fields_defined") is True
            and checks.get("metric_definition_no_longer_required") is True
            and checks.get("event_history_fields_recovered") is True
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _remaining_rmp_trajectory_field_recovery_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    needs_metric = summary.get("needs_metric_definition_fields", [])
    still_missing_or_partial = summary.get("still_missing_or_partial_fields", [])
    report_phrases = {
        "audit_current": "remaining_rmp_trajectory_field_recovery = current"
        in report_text,
        "case_count": "case_count = 82" in report_text,
        "production_ready": "production_ready_field_count = 8" in report_text,
        "needs_metric": (
            "needs_metric_definition_fields = " in report_text
        ),
        "needs_snapshot": (
            "needs_full_active_basis_capture_fields = active_basis_churn_count_before,rmp_degeneracy_pressure_before"
            in report_text
        ),
        "cannot_default_worker": "不能做：只因为 Pulse 能加 true-RC negative columns 就默认启用 worker"
        in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "case_count": _as_int(summary.get("case_count")),
        "source_file_exists_count": _as_int(summary.get("source_file_exists_count")),
        "remaining_field_count": _as_int(summary.get("remaining_field_count")),
        "production_ready_field_count": _as_int(
            summary.get("production_ready_field_count")
        ),
        "needs_metric_definition_fields": needs_metric,
        "needs_full_active_basis_capture_fields": summary.get(
            "needs_full_active_basis_capture_fields", []
        ),
        "still_missing_or_partial_fields": still_missing_or_partial,
        "field_status_counts": summary.get("field_status_counts", {}),
        "recommended_next_action": summary.get("recommended_next_action", ""),
        "report_phrase_presence": report_phrases,
        "check_remaining_rmp_trajectory_field_recovery_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("diagnostic_only") is True
            and summary.get("runs_bpc_or_pricing") is False
            and _as_int(summary.get("case_count")) == 82
            and _as_int(summary.get("source_file_exists_count")) == 82
            and _as_int(summary.get("remaining_field_count")) == 10
            and _as_int(summary.get("production_ready_field_count")) == 8
            and needs_metric == []
            and summary.get("needs_full_active_basis_capture_fields", [])
            == [
                "active_basis_churn_count_before",
                "rmp_degeneracy_pressure_before",
            ]
            and still_missing_or_partial
            == [
                "active_basis_churn_count_before",
                "rmp_degeneracy_pressure_before",
            ]
            and checks.get("some_fields_recoverable_now") is True
            and checks.get("some_fields_still_block_production_selector") is True
            and checks.get("metric_definition_no_longer_needed") is True
            and checks.get("full_active_basis_capture_still_needed") is True
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _active_basis_observability_gap_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "audit_current": "active_basis_observability_gap = current"
        in report_text,
        "manifest_cases": "manifest_case_count = 82" in report_text,
        "no_manifest_snapshot": (
            "cases_with_full_active_manifest_snapshot = 0" in report_text
        ),
        "no_event_snapshot": (
            "cases_with_full_active_event_snapshot = 0" in report_text
        ),
        "no_active_marker": (
            "cases_with_pool_journey_active_marker = 0" in report_text
        ),
        "not_reconstructable": (
            "exact_active_basis_churn_reconstructable_case_count = 0"
            in report_text
        ),
        "capture_schema_next": (
            "完整 active basis task sets / journey ids / lambda values"
            in report_text
        ),
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "manifest_case_count": _as_int(summary.get("manifest_case_count")),
        "source_file_exists_count": _as_int(summary.get("source_file_exists_count")),
        "cases_with_pool_journeys": _as_int(summary.get("cases_with_pool_journeys")),
        "cases_with_pool_journey_active_marker": _as_int(
            summary.get("cases_with_pool_journey_active_marker")
        ),
        "cases_with_full_active_manifest_snapshot": _as_int(
            summary.get("cases_with_full_active_manifest_snapshot")
        ),
        "cases_with_full_active_event_snapshot": _as_int(
            summary.get("cases_with_full_active_event_snapshot")
        ),
        "cases_with_active_hash": _as_int(summary.get("cases_with_active_hash")),
        "cases_with_truncated_active_top_samples": _as_int(
            summary.get("cases_with_truncated_active_top_samples")
        ),
        "exact_active_basis_churn_reconstructable_case_count": _as_int(
            summary.get("exact_active_basis_churn_reconstructable_case_count")
        ),
        "exact_rmp_degeneracy_pressure_reconstructable_case_count": _as_int(
            summary.get("exact_rmp_degeneracy_pressure_reconstructable_case_count")
        ),
        "active_basis_proxy_context_folds": _as_int(
            summary.get("active_basis_proxy_context_folds")
        ),
        "degeneracy_proxy_context_folds": _as_int(
            summary.get("degeneracy_proxy_context_folds")
        ),
        "best_multifeature_model": summary.get("best_multifeature_model"),
        "best_multifeature_context_folds": _as_int(
            summary.get("best_multifeature_context_folds")
        ),
        "robust_enriched_feature_count": _as_int(
            summary.get("robust_enriched_feature_count")
        ),
        "robust_model_count": _as_int(summary.get("robust_model_count")),
        "report_phrase_presence": report_phrases,
        "check_active_basis_observability_gap_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("diagnostic_only") is True
            and summary.get("runs_bpc_or_pricing") is False
            and _as_int(summary.get("manifest_case_count")) == 82
            and _as_int(summary.get("source_file_exists_count")) == 82
            and _as_int(summary.get("cases_with_pool_journeys")) == 82
            and _as_int(summary.get("cases_with_pool_journey_active_marker")) == 0
            and _as_int(summary.get("cases_with_full_active_manifest_snapshot")) == 0
            and _as_int(summary.get("cases_with_full_active_event_snapshot")) == 0
            and _as_int(summary.get("cases_with_active_hash")) >= 80
            and _as_int(summary.get("cases_with_truncated_active_top_samples")) > 0
            and _as_int(
                summary.get("exact_active_basis_churn_reconstructable_case_count")
            )
            == 0
            and _as_int(
                summary.get(
                    "exact_rmp_degeneracy_pressure_reconstructable_case_count"
                )
            )
            == 0
            and _as_int(summary.get("active_basis_proxy_context_folds")) == 14
            and _as_int(summary.get("degeneracy_proxy_context_folds")) == 9
            and summary.get("best_multifeature_model") == "shallow_tree_depth3"
            and _as_int(summary.get("best_multifeature_context_folds")) == 15
            and _as_int(summary.get("robust_enriched_feature_count")) == 0
            and _as_int(summary.get("robust_model_count")) == 0
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _active_basis_capture_schema_feasibility_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "audit_current": "active_basis_capture_schema_feasibility = current"
        in report_text,
        "all_fields_feasible": "missing_target_schema_field_count = 0"
        in report_text,
        "has_variable_values": "solution_has_variable_values = true"
        in report_text,
        "aggregate_only": "diagnostics_emits_full_snapshot = false"
        in report_text,
        "no_solver_change": "requires_solver_model_change = false"
        in report_text,
        "no_pricing_change": "requires_pricing_change = false" in report_text,
        "no_certificate_effect": "requires_certificate_effect = false"
        in report_text,
        "logging_guard": "requires_no_certificate_effect_logging_guard = true"
        in report_text,
        "capture_receives_values": (
            "counterfactual_capture_passes_active_variable_values = true"
            in report_text
        ),
        "capture_supports_snapshot": (
            "counterfactual_capture_supports_active_basis_snapshot = true"
            in report_text
        ),
        "implementation_default_off": (
            "capture_schema_implementation_status = implemented_default_off"
            in report_text
        ),
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "feasible_target_schema_field_count": _as_int(
            summary.get("feasible_target_schema_field_count")
        ),
        "missing_target_schema_field_count": _as_int(
            summary.get("missing_target_schema_field_count")
        ),
        "solution_has_variable_values": summary.get("solution_has_variable_values"),
        "solve_returns_full_variable_values": summary.get(
            "solve_returns_full_variable_values"
        ),
        "solve_can_return_reduced_costs": summary.get("solve_can_return_reduced_costs"),
        "driver_passes_variable_values_to_diagnostics": summary.get(
            "driver_passes_variable_values_to_diagnostics"
        ),
        "counterfactual_capture_passes_active_variable_values": summary.get(
            "counterfactual_capture_passes_active_variable_values"
        ),
        "counterfactual_capture_supports_active_basis_snapshot": summary.get(
            "counterfactual_capture_supports_active_basis_snapshot"
        ),
        "diagnostics_emits_full_snapshot": summary.get(
            "diagnostics_emits_full_snapshot"
        ),
        "capture_schema_implementation_status": summary.get(
            "capture_schema_implementation_status"
        ),
        "requires_solver_model_change": summary.get("requires_solver_model_change"),
        "requires_pricing_change": summary.get("requires_pricing_change"),
        "requires_certificate_effect": summary.get("requires_certificate_effect"),
        "requires_no_certificate_effect_logging_guard": summary.get(
            "requires_no_certificate_effect_logging_guard"
        ),
        "report_phrase_presence": report_phrases,
        "check_active_basis_capture_schema_feasibility_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("diagnostic_only") is True
            and summary.get("runs_bpc_or_pricing") is False
            and _as_int(summary.get("feasible_target_schema_field_count")) == 9
            and _as_int(summary.get("missing_target_schema_field_count")) == 0
            and summary.get("solution_has_journey_values") is True
            and summary.get("solution_has_variable_values") is True
            and summary.get("solution_has_reduced_costs") is True
            and summary.get("solve_returns_active_values") is True
            and summary.get("solve_returns_full_variable_values") is True
            and summary.get("solve_can_return_reduced_costs") is True
            and summary.get("driver_passes_active_values_to_diagnostics") is True
            and summary.get("driver_passes_variable_values_to_diagnostics") is False
            and summary.get("counterfactual_capture_passes_active_variable_values") is True
            and summary.get("counterfactual_capture_supports_active_basis_snapshot") is True
            and summary.get("diagnostics_emits_aggregate_active_fields") is True
            and summary.get("diagnostics_emits_full_snapshot") is False
            and summary.get("capture_schema_implementation_status") == "implemented_default_off"
            and summary.get("requires_solver_model_change") is False
            and summary.get("requires_pricing_change") is False
            and summary.get("requires_certificate_effect") is False
            and summary.get("requires_no_certificate_effect_logging_guard") is True
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _active_basis_snapshot_smoke_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "smoke_current": "Active-basis Snapshot Smoke" in report_text,
        "no_certificate_effect": "official_effect_count = 0" in report_text,
        "churn_populated": (
            f"active_basis_churn_nonempty_count = "
            f"{_as_int(summary.get('active_basis_churn_nonempty_count'))}"
        )
        in report_text,
        "degeneracy_populated": (
            f"rmp_degeneracy_pressure_nonempty_count = "
            f"{_as_int(summary.get('rmp_degeneracy_pressure_nonempty_count'))}"
        )
        in report_text,
        "not_speedup_proof": (
            "production selector" in report_text
            and "5/10 full no-regression" in report_text
            and "20-task wall-time speedup" in report_text
        ),
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "capture_event_count": _as_int(summary.get("capture_event_count")),
        "active_complete_capture_count": _as_int(
            summary.get("active_complete_capture_count")
        ),
        "active_basis_payload_count_min": _as_int(
            summary.get("active_basis_payload_count_min")
        ),
        "active_basis_payload_count_max": _as_int(
            summary.get("active_basis_payload_count_max")
        ),
        "impact_candidate_row_count": _as_int(
            summary.get("impact_candidate_row_count")
        ),
        "impact_high_impact_candidate_count": _as_int(
            summary.get("impact_high_impact_candidate_count")
        ),
        "impact_noop_candidate_count": _as_int(
            summary.get("impact_noop_candidate_count")
        ),
        "active_basis_churn_nonempty_count": _as_int(
            summary.get("active_basis_churn_nonempty_count")
        ),
        "rmp_degeneracy_pressure_nonempty_count": _as_int(
            summary.get("rmp_degeneracy_pressure_nonempty_count")
        ),
        "official_effect_count": _as_int(summary.get("official_effect_count")),
        "active_basis_churn_source_counts": summary.get(
            "active_basis_churn_source_counts", {}
        ),
        "report_phrase_presence": report_phrases,
        "check_active_basis_snapshot_smoke_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("runs_bpc_or_pricing") is False
            and _as_int(summary.get("capture_event_count")) > 0
            and _as_int(summary.get("active_complete_capture_count"))
            == _as_int(summary.get("capture_event_count"))
            and _as_int(summary.get("active_basis_payload_count_min")) > 0
            and _as_int(summary.get("impact_candidate_row_count")) > 0
            and _as_int(summary.get("active_basis_churn_nonempty_count"))
            == _as_int(summary.get("impact_candidate_row_count"))
            and _as_int(summary.get("rmp_degeneracy_pressure_nonempty_count"))
            == _as_int(summary.get("impact_candidate_row_count"))
            and _as_int(summary.get("official_effect_count")) == 0
            and bool(checks.get("all_capture_events_no_certificate_effect"))
            and bool(checks.get("active_basis_churn_populated_for_all_candidates"))
            and bool(
                checks.get("rmp_degeneracy_pressure_populated_for_all_candidates")
            )
            and all(report_phrases.values())
        ),
    }


def _active_basis_snapshot_mt20_smoke_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    metrics = _active_basis_snapshot_smoke_metrics(summary_path, report_path)
    metrics["check_active_basis_snapshot_mt20_smoke_is_current"] = bool(
        metrics["check_active_basis_snapshot_smoke_is_current"]
        and metrics["impact_high_impact_candidate_count"] == 1
        and metrics["impact_noop_candidate_count"] == 1
        and metrics["active_basis_payload_count_max"] >= 10
    )
    return metrics


def _active_basis_snapshot_multi20_smoke_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    metrics = _active_basis_snapshot_smoke_metrics(summary_path, report_path)
    metrics["check_active_basis_snapshot_multi20_smoke_is_current"] = bool(
        metrics["check_active_basis_snapshot_smoke_is_current"]
        and metrics["capture_event_count"] == 4
        and metrics["impact_candidate_row_count"] == 4
        and metrics["impact_high_impact_candidate_count"] == 4
        and metrics["impact_noop_candidate_count"] == 0
        and metrics["active_basis_payload_count_min"] >= 8
    )
    return metrics


def _active_basis_snapshot_greedy_apollo20_02_smoke_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    metrics = _active_basis_snapshot_smoke_metrics(summary_path, report_path)
    metrics["check_active_basis_snapshot_greedy_apollo20_02_smoke_is_current"] = bool(
        metrics["check_active_basis_snapshot_smoke_is_current"]
        and metrics["capture_event_count"] == 2
        and metrics["impact_candidate_row_count"] == 2
        and metrics["impact_high_impact_candidate_count"] == 2
        and metrics["impact_noop_candidate_count"] == 0
        and metrics["active_basis_payload_count_min"] >= 10
    )
    return metrics


def _active_basis_snapshot_greedy20_pair_smoke_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    metrics = _active_basis_snapshot_smoke_metrics(summary_path, report_path)
    metrics["check_active_basis_snapshot_greedy20_pair_smoke_is_current"] = bool(
        metrics["check_active_basis_snapshot_smoke_is_current"]
        and metrics["capture_event_count"] == 4
        and metrics["impact_candidate_row_count"] == 4
        and metrics["impact_high_impact_candidate_count"] == 3
        and metrics["impact_noop_candidate_count"] == 1
        and metrics["active_basis_payload_count_min"] >= 9
    )
    return metrics


def _active_basis_snapshot_selector_signal_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    label_counts = summary.get("label_counts", {})
    task20_label_counts = summary.get("task20_label_counts", {})
    task20_threshold = summary.get("task20_true_rc_threshold_metrics", {})
    report_phrases = {
        "title": "Active-basis Snapshot Selector Signal" in report_text,
        "false_positive": "false positive" in report_text,
        "not_production_selector": "production selector" in report_text,
        "not_no_regression_or_speedup": (
            "不是 5/10 no-regression 或 20-task speedup 证明" in report_text
        ),
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "row_count": _as_int(summary.get("row_count")),
        "task20_row_count": _as_int(summary.get("task20_row_count")),
        "label_counts": label_counts,
        "task20_label_counts": task20_label_counts,
        "task20_new_task_set_row_count": _as_int(
            summary.get("task20_new_task_set_row_count")
        ),
        "task20_true_rc_threshold_fp": _as_int(task20_threshold.get("fp")),
        "task20_true_rc_threshold_tp": _as_int(task20_threshold.get("tp")),
        "task20_true_rc_threshold_fn": _as_int(task20_threshold.get("fn")),
        "perfect_single_feature_rule_count": _as_int(
            summary.get("perfect_single_feature_rule_count")
        ),
        "runs_bpc_or_pricing": bool(summary.get("runs_bpc_or_pricing")),
        "checks": checks,
        "report_phrase_presence": report_phrases,
        "check_active_basis_snapshot_selector_signal_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("runs_bpc_or_pricing") is False
            and _as_int(summary.get("row_count")) == 14
            and _as_int(summary.get("task20_row_count")) == 12
            and _as_int(label_counts.get("improved")) == 11
            and _as_int(label_counts.get("noop")) == 3
            and _as_int(task20_label_counts.get("improved")) == 10
            and _as_int(task20_label_counts.get("noop")) == 2
            and _as_int(summary.get("task20_new_task_set_row_count")) == 12
            and _as_int(task20_threshold.get("fp")) > 0
            and _as_int(summary.get("perfect_single_feature_rule_count")) == 0
            and bool(checks.get("dataset_is_too_small_for_production_holdout"))
            and bool(checks.get("true_rc_threshold_has_false_positive_on_twenty"))
            and bool(checks.get("twenty_new_task_set_contains_high_and_noop"))
            and all(report_phrases.values())
        ),
    }


def _active_basis_snapshot_counterexamples_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    label_counts = summary.get("label_counts", {})
    task20_label_counts = summary.get("task20_label_counts", {})
    false_positive_rows = summary.get("false_positive_rows", [])
    positive_churn_label_counts = summary.get("positive_churn_label_counts", {})
    degeneracy_one_label_counts = summary.get("degeneracy_one_label_counts", {})
    mixed_instance_groups = summary.get("mixed_instance_groups", [])
    strongest_noop = summary.get("strongest_noop") or {}
    report_phrases = {
        "title": "Active-basis Snapshot Counterexamples" in report_text,
        "strongest_noop": "Strongest Noop" in report_text,
        "true_rc": "true-RC" in report_text,
        "new_task_set": "new-task-set" in report_text,
        "not_component_only": "Pulse 单组件或负列数量不足" in report_text,
        "not_single_scalar": "单个 snapshot scalar" in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "row_count": _as_int(summary.get("row_count")),
        "task20_row_count": _as_int(summary.get("task20_row_count")),
        "label_counts": label_counts,
        "task20_label_counts": task20_label_counts,
        "task20_new_task_set_row_count": _as_int(
            summary.get("task20_new_task_set_row_count")
        ),
        "false_positive_count": len(false_positive_rows),
        "strongest_noop_true_reduced_cost": strongest_noop.get("true_reduced_cost"),
        "weaker_improved_than_strongest_noop_count": _as_int(
            summary.get("weaker_improved_than_strongest_noop_count")
        ),
        "positive_churn_label_counts": positive_churn_label_counts,
        "degeneracy_one_label_counts": degeneracy_one_label_counts,
        "mixed_instance_group_count": len(mixed_instance_groups),
        "runs_bpc_or_pricing": bool(summary.get("runs_bpc_or_pricing")),
        "checks": checks,
        "report_phrase_presence": report_phrases,
        "check_active_basis_snapshot_counterexamples_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("runs_bpc_or_pricing") is False
            and _as_int(summary.get("row_count")) == 14
            and _as_int(summary.get("task20_row_count")) == 12
            and _as_int(label_counts.get("improved")) == 11
            and _as_int(label_counts.get("noop")) == 3
            and _as_int(task20_label_counts.get("improved")) == 10
            and _as_int(task20_label_counts.get("noop")) == 2
            and _as_int(summary.get("task20_new_task_set_row_count")) == 12
            and len(false_positive_rows) >= 2
            and _as_int(summary.get("weaker_improved_than_strongest_noop_count")) > 0
            and _as_int(positive_churn_label_counts.get("improved")) > 0
            and _as_int(positive_churn_label_counts.get("noop")) > 0
            and _as_int(degeneracy_one_label_counts.get("improved")) > 0
            and _as_int(degeneracy_one_label_counts.get("noop")) > 0
            and bool(mixed_instance_groups)
            and bool(checks.get("task20_rows_are_all_new_task_set"))
            and bool(checks.get("true_rc_threshold_has_task20_false_positives"))
            and bool(checks.get("strongest_noop_more_negative_than_some_improved"))
            and bool(checks.get("positive_churn_contains_high_and_noop"))
            and bool(checks.get("degeneracy_one_contains_high_and_noop"))
            and bool(checks.get("has_mixed_task20_instance_group"))
            and all(report_phrases.values())
        ),
    }


def _selector_enriched_rmp_feature_holdout_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    best = summary.get("best_by_feature", {})
    control_context = best.get("control_objective", {}).get("context_hash", {})
    rmp_context = best.get("rmp_objective_before", {}).get("context_hash", {})
    dual_l1_context = best.get("dual_l1_norm_before", {}).get("context_hash", {})
    pool_context = best.get("column_pool_size_before", {}).get("context_hash", {})
    recent_objective_context = best.get("recent_objective_delta_before", {}).get(
        "context_hash", {}
    )
    basis_churn_context = best.get(
        "active_basis_hash_churn_count_before", {}
    ).get("context_hash", {})
    basis_unique_context = best.get(
        "active_basis_hash_unique_count_before", {}
    ).get("context_hash", {})
    degeneracy_proxy_context = best.get(
        "rmp_degeneracy_proxy_score_before", {}
    ).get("context_hash", {})
    report_phrases = {
        "audit_current": "selector_enriched_rmp_feature_holdout = current"
        in report_text,
        "row_count": "row_count = 280" in report_text,
        "robust_enriched_zero": "robust_all_holdout_enriched_feature_count = 0"
        in report_text,
        "robust_numeric_zero": "robust_all_holdout_numeric_feature_count = 0"
        in report_text,
        "control_context": "control_objective_context_folds = 13/28"
        in report_text,
        "best_enriched": "best_enriched_feature = recent_objective_delta_before"
        in report_text,
        "production_blocked": (
            "仍不是 production selector" in report_text
            or "仍不能形成 production selector" in report_text
        ),
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "row_count": _as_int(summary.get("row_count")),
        "label_counts": dict(summary.get("label_counts", {}) or {}),
        "enriched_rmp_features": list(summary.get("enriched_rmp_features", []) or []),
        "robust_all_holdout_enriched_feature_count": len(
            summary.get("robust_all_holdout_enriched_features", []) or []
        ),
        "robust_all_holdout_numeric_feature_count": len(
            summary.get("robust_all_holdout_numeric_features", []) or []
        ),
        "control_objective_context_passing_folds": _as_int(
            control_context.get("passing_fold_count")
        ),
        "rmp_objective_context_passing_folds": _as_int(
            rmp_context.get("passing_fold_count")
        ),
        "dual_l1_context_passing_folds": _as_int(
            dual_l1_context.get("passing_fold_count")
        ),
        "column_pool_context_passing_folds": _as_int(
            pool_context.get("passing_fold_count")
        ),
        "recent_objective_context_passing_folds": _as_int(
            recent_objective_context.get("passing_fold_count")
        ),
        "active_basis_hash_churn_context_passing_folds": _as_int(
            basis_churn_context.get("passing_fold_count")
        ),
        "active_basis_hash_unique_context_passing_folds": _as_int(
            basis_unique_context.get("passing_fold_count")
        ),
        "rmp_degeneracy_proxy_context_passing_folds": _as_int(
            degeneracy_proxy_context.get("passing_fold_count")
        ),
        "report_phrase_presence": report_phrases,
        "check_selector_enriched_rmp_feature_holdout_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("diagnostic_only") is True
            and summary.get("runs_bpc_or_pricing") is False
            and _as_int(summary.get("row_count")) == 280
            and summary.get("label_counts", {}).get("improved") == 209
            and summary.get("label_counts", {}).get("noop") == 71
            and len(summary.get("enriched_rmp_features", []) or []) == 16
            and summary.get("robust_all_holdout_enriched_features") == []
            and summary.get("robust_all_holdout_numeric_features") == []
            and _as_int(control_context.get("passing_fold_count")) == 13
            and _as_int(control_context.get("fold_count")) == 28
            and _as_int(rmp_context.get("passing_fold_count")) == 13
            and _as_int(rmp_context.get("fold_count")) == 28
            and _as_int(dual_l1_context.get("passing_fold_count")) == 16
            and _as_int(pool_context.get("passing_fold_count")) == 15
            and _as_int(recent_objective_context.get("passing_fold_count")) == 17
            and _as_int(recent_objective_context.get("fold_count")) == 28
            and _as_int(basis_churn_context.get("passing_fold_count")) == 14
            and _as_int(basis_unique_context.get("passing_fold_count")) == 14
            and _as_int(degeneracy_proxy_context.get("passing_fold_count")) == 9
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _selector_enriched_multifeature_model_holdout_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    holdout_by_model = summary.get("holdout_by_model", {})
    best_model = str(summary.get("best_context_model", ""))
    best_payload = holdout_by_model.get(best_model, {})
    best_context = best_payload.get("context_hash", {})
    best_instance = best_payload.get("instance", {})
    best_dataset = best_payload.get("impact_dataset", {})
    report_phrases = {
        "audit_current": "selector_enriched_multifeature_model_holdout = current"
        in report_text,
        "row_count": "row_count = 280" in report_text,
        "best_model": "best_context_model = shallow_tree_depth3" in report_text,
        "robust_zero": "robust_all_holdout_model_count = 0" in report_text,
        "production_false": "production_validated_selector = false" in report_text,
        "still_blocked": "还不能作为" in report_text or "不能作为" in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "row_count": _as_int(summary.get("row_count")),
        "label_counts": dict(summary.get("label_counts", {}) or {}),
        "model_features_count": len(summary.get("model_features", []) or []),
        "enriched_features_count": len(summary.get("enriched_features", []) or []),
        "best_context_model": best_model,
        "best_context_model_context_folds": _as_int(
            best_context.get("passing_fold_count")
        ),
        "best_context_model_instance_folds": _as_int(
            best_instance.get("passing_fold_count")
        ),
        "best_context_model_dataset_folds": _as_int(
            best_dataset.get("passing_fold_count")
        ),
        "robust_all_holdout_model_count": len(
            summary.get("robust_all_holdout_models", []) or []
        ),
        "report_phrase_presence": report_phrases,
        "check_selector_enriched_multifeature_model_holdout_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("diagnostic_only") is True
            and summary.get("runs_bpc_or_pricing") is False
            and _as_int(summary.get("row_count")) == 280
            and summary.get("label_counts", {}).get("improved") == 209
            and summary.get("label_counts", {}).get("noop") == 71
            and len(summary.get("model_features", []) or []) == 27
            and len(summary.get("enriched_features", []) or []) == 18
            and best_model == "shallow_tree_depth3"
            and _as_int(best_context.get("passing_fold_count")) == 15
            and _as_int(best_context.get("fold_count")) == 28
            and _as_int(best_instance.get("passing_fold_count")) == 1
            and _as_int(best_instance.get("fold_count")) == 4
            and _as_int(best_dataset.get("passing_fold_count")) == 4
            and _as_int(best_dataset.get("fold_count")) == 5
            and summary.get("robust_all_holdout_models") == []
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _optimization_direction_candidate_registry_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    candidates = list(summary.get("candidates", []))
    direction_ids = [str(item.get("direction_id", "")) for item in candidates]
    expected_direction_ids = [
        "pulse_wiring_or_certificate_semantics",
        "more_true_rc_negative_columns",
        "expand_worker_budget_or_default_worker",
        "true_rc_threshold_or_local_column_selector",
        "simple_ml_or_batch_selector",
        "simple_rmp_trajectory_proxy_selector",
        "single_context_or_local_replay_success",
        "exact_context_capture_and_replay_dataset",
        "addition_before_selector",
        "production_candidate_ab",
        "official_certificate_gate",
    ]
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "registry_current": (
            "optimization_direction_candidate_registry = current" in report_text
        ),
        "approved_zero": "approved_production_direction_count = 0" in report_text,
        "production_false": "production_direction_proven = false" in report_text,
        "goal_false": "goal_complete = false" in report_text,
        "stage": (
            "current_allowed_next_stage = calibration_only_selector_holdout"
            in report_text
        ),
        "answer": "不是 Pulse 子模块单点失效" in report_text,
        "worker_forbidden": "forbidden_for_current_stage" in report_text,
        "selector_holdout": "calibration_only_not_production_validated"
        in report_text,
    }
    statuses = {
        str(item.get("direction_id", "")): str(item.get("status", ""))
        for item in candidates
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "candidate_count": _as_int(summary.get("candidate_count")),
        "approved_production_direction_count": _as_int(
            summary.get("approved_production_direction_count")
        ),
        "forbidden_direction_count": _as_int(
            summary.get("forbidden_direction_count")
        ),
        "allowed_calibration_direction_count": _as_int(
            summary.get("allowed_calibration_direction_count")
        ),
        "current_allowed_next_stage": summary.get("current_allowed_next_stage"),
        "production_direction_proven": summary.get("production_direction_proven"),
        "goal_complete": summary.get("goal_complete"),
        "missing_requirements": summary.get("missing_requirements"),
        "direction_ids": direction_ids,
        "direction_statuses": statuses,
        "report_phrase_presence": report_phrases,
        "check_optimization_direction_registry_is_current": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and _as_int(summary.get("candidate_count")) == 11
            and _as_int(summary.get("approved_production_direction_count")) == 0
            and summary.get("production_direction_proven") is False
            and summary.get("goal_complete") is False
            and summary.get("current_allowed_next_stage")
            == "calibration_only_selector_holdout"
            and summary.get("missing_requirements")
            == [
                "five_ten_full_no_regression_ab",
                "production_validated_selector",
                "twenty_walltime_speedup",
            ]
            and direction_ids == expected_direction_ids
            and statuses.get("more_true_rc_negative_columns")
            == "ruled_out_as_sufficient_condition"
            and statuses.get("expand_worker_budget_or_default_worker")
            == "forbidden_for_current_stage"
            and statuses.get("addition_before_selector")
            == "calibration_only_not_production_validated"
            and statuses.get("production_candidate_ab") == "blocked"
            and statuses.get("official_certificate_gate")
            == "forbidden_for_current_stage"
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _selector_threshold_frontier_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    recommended = summary.get("recommended_threshold_metrics", {})
    best_f1 = summary.get("best_f1_threshold_metrics", {})
    zero_fp = summary.get("best_zero_false_positive_threshold_metrics", {})
    zero_fn = summary.get("best_zero_false_negative_threshold_metrics", {})
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "perfect_zero": "perfect_threshold_count = 0" in report_text,
        "zero_fp_recall": "recall': 0.267942583732" in report_text,
        "zero_fn_fp": "'fp': 62" in report_text,
        "not_simple_threshold": "不是简单调 true-RC 阈值即可解决" in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "row_count": _as_int(summary.get("row_count")),
        "threshold_count": _as_int(summary.get("threshold_count")),
        "perfect_threshold_count": _as_int(summary.get("perfect_threshold_count")),
        "recommended_fp": _as_int(recommended.get("fp")),
        "recommended_fn": _as_int(recommended.get("fn")),
        "best_f1_fp": _as_int(best_f1.get("fp")),
        "best_f1_fn": _as_int(best_f1.get("fn")),
        "zero_fp_recall": _as_float(zero_fp.get("recall")),
        "zero_fn_fp": _as_int(zero_fn.get("fp")),
        "report_phrase_presence": report_phrases,
        "check_threshold_frontier_rules_out_simple_threshold": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and _as_int(summary.get("row_count")) == 280
            and _as_int(summary.get("perfect_threshold_count")) == 0
            and _as_int(recommended.get("fp")) > 0
            and _as_int(recommended.get("fn")) > 0
            and _as_int(best_f1.get("fp")) > 0
            and _as_int(best_f1.get("fn")) > 0
            and (_as_float(zero_fp.get("recall")) or 0.0) < 0.5
            and _as_int(zero_fn.get("fp")) > 0
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _selector_context_collision_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    groups = summary.get("group_summaries", {})
    task_set = groups.get("task_set", {})
    task_sequence = groups.get("task_sequence", {})
    online_flags = groups.get("online_flags", {})
    task_flags = groups.get("task_flags", {})
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "task_set_mixed": "task_set_mixed_group_count = 6" in report_text,
        "task_sequence_mixed": "task_sequence_mixed_group_count = 5"
        in report_text,
        "online_flags_mixed": "online_flags_mixed_row_count = 278"
        in report_text,
        "not_column_local": "不能只依赖列局部特征" in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "row_count": _as_int(summary.get("row_count")),
        "task_set_group_count": _as_int(task_set.get("group_count")),
        "task_set_mixed_group_count": _as_int(task_set.get("mixed_group_count")),
        "task_set_mixed_row_count": _as_int(task_set.get("mixed_row_count")),
        "task_sequence_group_count": _as_int(task_sequence.get("group_count")),
        "task_sequence_mixed_group_count": _as_int(
            task_sequence.get("mixed_group_count")
        ),
        "task_sequence_mixed_row_count": _as_int(task_sequence.get("mixed_row_count")),
        "online_flags_group_count": _as_int(online_flags.get("group_count")),
        "online_flags_mixed_group_count": _as_int(
            online_flags.get("mixed_group_count")
        ),
        "online_flags_mixed_row_count": _as_int(online_flags.get("mixed_row_count")),
        "task_flags_group_count": _as_int(task_flags.get("group_count")),
        "task_flags_mixed_group_count": _as_int(
            task_flags.get("mixed_group_count")
        ),
        "task_flags_mixed_row_count": _as_int(task_flags.get("mixed_row_count")),
        "report_phrase_presence": report_phrases,
        "check_selector_context_collision_blocks_column_local_selector": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and _as_int(summary.get("row_count")) == 280
            and _as_int(task_set.get("mixed_group_count")) == 6
            and _as_int(task_set.get("mixed_row_count")) == 41
            and _as_int(task_sequence.get("mixed_group_count")) == 5
            and _as_int(task_sequence.get("mixed_row_count")) == 30
            and _as_int(online_flags.get("mixed_group_count")) == 2
            and _as_int(online_flags.get("mixed_row_count")) == 278
            and _as_int(task_flags.get("mixed_group_count")) == 6
            and _as_int(task_flags.get("mixed_row_count")) == 41
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _selector_local_feature_direction_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    groups = summary.get("group_summaries", {})
    task_set = groups.get("task_set", {})
    task_sequence = groups.get("task_sequence", {})
    task_set_true_rc = task_set.get("feature_stats", {}).get(
        "true_reduced_cost", {}
    )
    task_sequence_true_rc = task_sequence.get("feature_stats", {}).get(
        "true_reduced_cost", {}
    )
    task_set_cost = task_set.get("feature_stats", {}).get("cost", {})
    task_sequence_cost = task_sequence.get("feature_stats", {}).get("cost", {})
    task_set_true_rc_counts = task_set_true_rc.get("direction_counts", {})
    task_sequence_true_rc_counts = task_sequence_true_rc.get(
        "direction_counts", {}
    )
    task_set_cost_counts = task_set_cost.get("direction_counts", {})
    task_sequence_cost_counts = task_sequence_cost.get("direction_counts", {})
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "task_set_true_rc_flip": (
            "task_set_true_rc_direction_counts = {'improved_lower_mean': 2, 'noop_lower_mean': 4}"
            in report_text
        ),
        "task_sequence_true_rc_flip": (
            "task_sequence_true_rc_direction_counts = {'noop_lower_mean': 3, 'improved_lower_mean': 2}"
            in report_text
        ),
        "not_monotone": "简单的列局部单调规则" in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "row_count": _as_int(summary.get("row_count")),
        "task_set_true_rc_improved_lower_count": _as_int(
            task_set_true_rc_counts.get("improved_lower_mean")
        ),
        "task_set_true_rc_noop_lower_count": _as_int(
            task_set_true_rc_counts.get("noop_lower_mean")
        ),
        "task_sequence_true_rc_improved_lower_count": _as_int(
            task_sequence_true_rc_counts.get("improved_lower_mean")
        ),
        "task_sequence_true_rc_noop_lower_count": _as_int(
            task_sequence_true_rc_counts.get("noop_lower_mean")
        ),
        "task_set_cost_direction_count": _as_int(
            task_set_cost.get("nonzero_direction_count")
        ),
        "task_sequence_cost_direction_count": _as_int(
            task_sequence_cost.get("nonzero_direction_count")
        ),
        "report_phrase_presence": report_phrases,
        "check_selector_local_feature_direction_blocks_monotone_selector": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and _as_int(summary.get("row_count")) == 280
            and _as_int(task_set_true_rc_counts.get("improved_lower_mean")) == 2
            and _as_int(task_set_true_rc_counts.get("noop_lower_mean")) == 4
            and _as_int(task_sequence_true_rc_counts.get("improved_lower_mean"))
            == 2
            and _as_int(task_sequence_true_rc_counts.get("noop_lower_mean")) == 3
            and _as_int(task_set_cost.get("nonzero_direction_count")) > 1
            and _as_int(task_sequence_cost.get("nonzero_direction_count")) > 1
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _selector_context_disambiguation_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    ladder = summary.get("ladder", {})
    local_sequence = ladder.get("local_sequence", {})
    online_instance = ladder.get("local_sequence_online_instance", {})
    dataset = ladder.get("local_sequence_online_dataset", {})
    context_hash = ladder.get("local_sequence_online_context_hash", {})
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "local_sequence_mixed": (
            "local_sequence_mixed_group_count = 5" in report_text
        ),
        "online_instance_mixed": (
            "local_sequence_online_instance_mixed_group_count = 5" in report_text
        ),
        "dataset_reduces": (
            "local_sequence_online_dataset_mixed_group_count = 1" in report_text
        ),
        "context_hash_zero": (
            "local_sequence_online_context_hash_mixed_group_count = 0"
            in report_text
        ),
        "not_production_selector": "不能直接作为 production addition-before selector"
        in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "row_count": _as_int(summary.get("row_count")),
        "local_sequence_group_count": _as_int(local_sequence.get("group_count")),
        "local_sequence_mixed_group_count": _as_int(
            local_sequence.get("mixed_group_count")
        ),
        "local_sequence_mixed_row_count": _as_int(
            local_sequence.get("mixed_row_count")
        ),
        "online_instance_mixed_group_count": _as_int(
            online_instance.get("mixed_group_count")
        ),
        "online_instance_mixed_row_count": _as_int(
            online_instance.get("mixed_row_count")
        ),
        "dataset_mixed_group_count": _as_int(dataset.get("mixed_group_count")),
        "dataset_mixed_row_count": _as_int(dataset.get("mixed_row_count")),
        "context_hash_group_count": _as_int(context_hash.get("group_count")),
        "context_hash_mixed_group_count": _as_int(
            context_hash.get("mixed_group_count")
        ),
        "context_hash_mixed_row_count": _as_int(
            context_hash.get("mixed_row_count")
        ),
        "report_phrase_presence": report_phrases,
        "check_context_disambiguation_supports_context_coupling": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and _as_int(summary.get("row_count")) == 280
            and _as_int(local_sequence.get("mixed_group_count")) == 5
            and _as_int(local_sequence.get("mixed_row_count")) == 30
            and _as_int(online_instance.get("mixed_group_count")) == 5
            and _as_int(online_instance.get("mixed_row_count")) == 30
            and _as_int(dataset.get("mixed_group_count")) == 1
            and _as_int(dataset.get("mixed_row_count")) == 6
            and _as_int(context_hash.get("mixed_group_count")) == 0
            and _as_int(context_hash.get("mixed_row_count")) == 0
            and _as_int(context_hash.get("group_count"))
            > _as_int(local_sequence.get("group_count"))
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _selector_context_scalar_candidates_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    groups = summary.get("groups", {})
    base = groups.get("base", {})
    cheap = groups.get("base_instance_cg_pricing", {})
    control_exact = groups.get("base_control_objective_exact", {})
    control_bin = groups.get("base_control_objective_bin_100", {})
    context_hash = groups.get("base_context_hash", {})
    checks = summary.get("checks", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "title": "Selector Context Scalar Candidate" in report_text,
        "base_mixed": "base_mixed_group_count = 5" in report_text,
        "cheap_mixed": (
            "base_instance_cg_pricing_mixed_group_count = 3" in report_text
        ),
        "control_bin_zero": (
            "control_objective_bin_100_mixed_group_count = 0" in report_text
        ),
        "context_hash_zero": "context_hash_mixed_group_count = 0" in report_text,
        "not_production": "不是 production selector 证明" in report_text,
        "holdout_required": "必须先通过 context / instance / dataset holdout"
        in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "row_count": _as_int(summary.get("row_count")),
        "base_mixed_group_count": _as_int(base.get("mixed_group_count")),
        "base_mixed_row_count": _as_int(base.get("mixed_row_count")),
        "cheap_scalar_mixed_group_count": _as_int(cheap.get("mixed_group_count")),
        "cheap_scalar_mixed_row_count": _as_int(cheap.get("mixed_row_count")),
        "control_objective_exact_group_count": _as_int(
            control_exact.get("group_count")
        ),
        "control_objective_exact_mixed_group_count": _as_int(
            control_exact.get("mixed_group_count")
        ),
        "control_objective_bin_100_group_count": _as_int(
            control_bin.get("group_count")
        ),
        "control_objective_bin_100_mixed_group_count": _as_int(
            control_bin.get("mixed_group_count")
        ),
        "context_hash_group_count": _as_int(context_hash.get("group_count")),
        "context_hash_mixed_group_count": _as_int(
            context_hash.get("mixed_group_count")
        ),
        "report_phrase_presence": report_phrases,
        "check_context_scalar_candidate_is_calibration_only": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and _as_int(summary.get("row_count")) == 280
            and _as_int(base.get("mixed_group_count")) == 5
            and _as_int(base.get("mixed_row_count")) == 30
            and _as_int(cheap.get("mixed_group_count")) == 3
            and _as_int(cheap.get("mixed_row_count")) == 18
            and _as_int(control_exact.get("mixed_group_count")) == 0
            and _as_int(control_bin.get("mixed_group_count")) == 0
            and _as_int(context_hash.get("mixed_group_count")) == 0
            and _as_int(control_bin.get("group_count"))
            < _as_int(context_hash.get("group_count"))
            and all(checks.values())
            and all(report_phrases.values())
        ),
    }


def _selector_context_scalar_holdout_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    models = summary.get("model_results", {})
    threshold = models.get("threshold_precision75", {})
    bin100 = models.get("bin100_majority75", {})
    threshold_context = (
        threshold.get("holdouts", {})
        .get("context_hash", {})
        .get("aggregate_metrics", {})
    )
    bin100_instance = (
        bin100.get("holdouts", {}).get("instance", {}).get("aggregate_metrics", {})
    )
    bin100_context = (
        bin100.get("holdouts", {}).get("context_hash", {}).get("aggregate_metrics", {})
    )
    checks = summary.get("checks", {})
    passing_models = summary.get("passing_models", [])
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "title": "Selector Context Scalar Holdout" in report_text,
        "current": "selector_context_scalar_holdout = current" in report_text,
        "passing_count_zero": (
            "control_objective_holdout_passing_model_count = 0" in report_text
        ),
        "production_false": (
            "control_objective_holdout_production_validated_selector = false"
            in report_text
        ),
        "threshold_context_precision": (
            "threshold_context_precision = 0.746377" in report_text
        ),
        "bin100_context_recall": (
            "bin100_context_recall = 0.339713" in report_text
        ),
        "not_production": "还不是 production selector" in report_text,
        "no_production_worker": (
            "不应把该 selector 接入 production worker" in report_text
        ),
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "row_count": _as_int(summary.get("row_count")),
        "passing_model_count": len(passing_models),
        "production_validated_selector": summary.get(
            "production_validated_selector"
        ),
        "threshold_context_precision": _as_float(
            threshold_context.get("precision")
        ),
        "threshold_context_recall": _as_float(threshold_context.get("recall")),
        "bin100_instance_precision": _as_float(bin100_instance.get("precision")),
        "bin100_instance_recall": _as_float(bin100_instance.get("recall")),
        "bin100_context_precision": _as_float(bin100_context.get("precision")),
        "bin100_context_recall": _as_float(bin100_context.get("recall")),
        "report_phrase_presence": report_phrases,
        "check_context_scalar_holdout_rejects_simple_rules": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and _as_int(summary.get("row_count")) == 280
            and len(passing_models) == 0
            and summary.get("production_validated_selector") is False
            and checks.get("threshold_high_recall_but_context_precision_fails")
            is True
            and checks.get("bin100_high_precision_but_instance_recall_fails")
            is True
            and checks.get("bin100_high_precision_but_context_recall_fails")
            is True
            and checks.get("no_model_passes_all_holdout_gates") is True
            and (_as_float(threshold_context.get("precision")) or 0.0) < 0.75
            and (_as_float(threshold_context.get("recall")) or 0.0) >= 0.5
            and (_as_float(bin100_context.get("precision")) or 0.0) >= 0.75
            and (_as_float(bin100_context.get("recall")) or 0.0) < 0.5
            and all(report_phrases.values())
        ),
    }


def _selector_micro_vs_fold_gate_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    features = summary.get("feature_summaries", {})
    true_rc_context = (
        features.get("true_reduced_cost", {})
        .get("holdouts", {})
        .get("context_hash", {})
    )
    new_task_dataset = (
        features.get("new_task_set", {})
        .get("holdouts", {})
        .get("impact_dataset", {})
    )
    true_rc_context_micro = true_rc_context.get("micro", {})
    new_task_dataset_micro = new_task_dataset.get("micro", {})
    checks = summary.get("checks", {})
    micro_passing_features = list(summary.get("micro_passing_features", []) or [])
    robust_features = list(
        summary.get("robust_all_fold_passing_features", []) or []
    )
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "title": "Selector Micro-vs-Fold Gate" in report_text,
        "current": "selector_micro_vs_fold_gate = current" in report_text,
        "micro_features": (
            "micro_passing_features = ['true_reduced_cost', 'cost', 'new_task_set', 'strict_replacement_by_cost']"
            in report_text
        ),
        "robust_zero": "robust_all_fold_passing_feature_count = 0" in report_text,
        "true_rc_context_folds": (
            "true_rc_context_passing_folds = 13/28" in report_text
        ),
        "new_task_dataset_folds": (
            "new_task_set_dataset_passing_folds = 3/5" in report_text
        ),
        "production_false": "production_validated_selector = false" in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "row_count": _as_int(summary.get("row_count")),
        "micro_passing_feature_count": len(micro_passing_features),
        "robust_all_fold_passing_feature_count": len(robust_features),
        "true_rc_context_precision": _as_float(
            true_rc_context_micro.get("precision")
        ),
        "true_rc_context_recall": _as_float(true_rc_context_micro.get("recall")),
        "true_rc_context_passing_fold_count": _as_int(
            true_rc_context.get("passing_fold_count")
        ),
        "true_rc_context_fold_count": _as_int(true_rc_context.get("fold_count")),
        "new_task_set_dataset_precision": _as_float(
            new_task_dataset_micro.get("precision")
        ),
        "new_task_set_dataset_recall": _as_float(
            new_task_dataset_micro.get("recall")
        ),
        "new_task_set_dataset_passing_fold_count": _as_int(
            new_task_dataset.get("passing_fold_count")
        ),
        "new_task_set_dataset_fold_count": _as_int(
            new_task_dataset.get("fold_count")
        ),
        "report_phrase_presence": report_phrases,
        "check_micro_average_gate_is_not_production_selector": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and _as_int(summary.get("row_count")) == 280
            and len(micro_passing_features) == 4
            and len(robust_features) == 0
            and checks.get("has_micro_passing_features") is True
            and checks.get("no_micro_feature_passes_all_fold_gates") is True
            and checks.get("true_rc_micro_passes_but_context_folds_fail") is True
            and checks.get("new_task_set_micro_passes_but_dataset_folds_fail")
            is True
            and _as_int(true_rc_context.get("passing_fold_count")) == 13
            and _as_int(true_rc_context.get("fold_count")) == 28
            and _as_int(new_task_dataset.get("passing_fold_count")) == 3
            and _as_int(new_task_dataset.get("fold_count")) == 5
            and all(report_phrases.values())
        ),
    }


def _selector_model_micro_vs_fold_gate_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    models = summary.get("model_summaries", {})
    nearest_context = (
        models.get("nearest_centroid", {})
        .get("holdouts", {})
        .get("leave_one_context", {})
    )
    shallow_dataset = (
        models.get("shallow_tree_depth3", {})
        .get("holdouts", {})
        .get("leave_one_dataset", {})
    )
    nearest_context_aggregate = nearest_context.get("aggregate", {})
    shallow_dataset_aggregate = shallow_dataset.get("aggregate", {})
    checks = summary.get("checks", {})
    aggregate_models = list(summary.get("aggregate_all_holdout_models", []) or [])
    robust_models = list(summary.get("robust_all_fold_passing_models", []) or [])
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "title": "Selector Model Micro-vs-Fold Gate" in report_text,
        "current": "selector_model_micro_vs_fold_gate = current" in report_text,
        "aggregate_models": (
            "aggregate_all_holdout_models = ['nearest_centroid', 'shallow_tree_depth3']"
            in report_text
        ),
        "robust_zero": "robust_all_fold_passing_model_count = 0" in report_text,
        "nearest_context_folds": (
            "nearest_centroid_context_passing_folds = 16/28" in report_text
        ),
        "shallow_dataset_folds": (
            "shallow_tree_dataset_passing_folds = 4/5" in report_text
        ),
        "production_false": "production_validated_selector = false" in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "row_count": _as_int(summary.get("row_count")),
        "aggregate_all_holdout_model_count": len(aggregate_models),
        "robust_all_fold_passing_model_count": len(robust_models),
        "nearest_context_precision": _as_float(
            nearest_context_aggregate.get("precision")
        ),
        "nearest_context_recall": _as_float(
            nearest_context_aggregate.get("recall")
        ),
        "nearest_context_passing_fold_count": _as_int(
            nearest_context.get("passing_fold_count")
        ),
        "nearest_context_fold_count": _as_int(nearest_context.get("fold_count")),
        "shallow_dataset_precision": _as_float(
            shallow_dataset_aggregate.get("precision")
        ),
        "shallow_dataset_recall": _as_float(shallow_dataset_aggregate.get("recall")),
        "shallow_dataset_passing_fold_count": _as_int(
            shallow_dataset.get("passing_fold_count")
        ),
        "shallow_dataset_fold_count": _as_int(shallow_dataset.get("fold_count")),
        "report_phrase_presence": report_phrases,
        "check_model_aggregate_gate_is_not_production_selector": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and _as_int(summary.get("row_count")) == 280
            and aggregate_models == ["nearest_centroid", "shallow_tree_depth3"]
            and len(robust_models) == 0
            and checks.get("has_aggregate_all_holdout_models") is True
            and checks.get("no_aggregate_model_passes_all_fold_gates") is True
            and checks.get("nearest_centroid_context_folds_fail") is True
            and checks.get("shallow_tree_dataset_folds_fail") is True
            and _as_int(nearest_context.get("passing_fold_count")) == 16
            and _as_int(nearest_context.get("fold_count")) == 28
            and _as_int(shallow_dataset.get("passing_fold_count")) == 4
            and _as_int(shallow_dataset.get("fold_count")) == 5
            and all(report_phrases.values())
        ),
    }


def _selector_rule_family_search_metrics(
    summary_path: Path,
    report_path: Path,
    *,
    expected_row_count: int = 280,
    expected_rule_count_min: int = 18000,
    expected_task_count_filter: int | None = None,
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    top_rules = list(summary.get("top_full_sample_rules", []) or [])
    best_rule = top_rules[0] if top_rules else {}
    best_metrics = dict(best_rule.get("full_sample", {}) or {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "title": "Selector Rule-Family Search" in report_text,
        "current": "selector_rule_family_search = current" in report_text,
        "task_count_filter": (
            f"task_count_filter = {expected_task_count_filter}" in report_text
        ),
        "rule_count": f"rule_count = {summary.get('rule_count')}" in report_text,
        "strict_zero": "strict_all_fold_passing_rule_count = 0" in report_text,
        "material_zero": "material_all_fold_passing_rule_count = 0" in report_text,
        "best_rule": "cost>=73.9194 AND true_reduced_cost<=-3.82619"
        in report_text,
        "production_false": "production_validated_selector = false" in report_text,
        "not_production_worker": "不能把这些" in report_text
        and "接入 production worker" in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "row_count": _as_int(summary.get("row_count")),
        "single_clause_count": _as_int(summary.get("single_clause_count")),
        "rule_count": _as_int(summary.get("rule_count")),
        "strict_all_fold_passing_rule_count": _as_int(
            summary.get("strict_all_fold_passing_rule_count")
        ),
        "material_all_fold_passing_rule_count": _as_int(
            summary.get("material_all_fold_passing_rule_count")
        ),
        "best_rule_description": best_rule.get("description"),
        "best_rule_precision": _as_float(best_metrics.get("precision")),
        "best_rule_recall": _as_float(best_metrics.get("recall")),
        "best_rule_fp": _as_int(best_metrics.get("fp")),
        "best_rule_fn": _as_int(best_metrics.get("fn")),
        "report_phrase_presence": report_phrases,
        "check_rule_family_search_rejects_simple_conjunctions": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("feature_scope") == "addition_before_only"
            and summary.get("row_filter", {}).get("task_count")
            == expected_task_count_filter
            and _as_int(summary.get("row_count")) == expected_row_count
            and _as_int(summary.get("single_clause_count")) >= 900
            and _as_int(summary.get("rule_count")) >= expected_rule_count_min
            and _as_int(summary.get("strict_all_fold_passing_rule_count")) == 0
            and _as_int(summary.get("material_all_fold_passing_rule_count")) == 0
            and checks.get("top_full_sample_has_signal") is True
            and checks.get("no_strict_all_fold_rule") is True
            and checks.get("no_material_all_fold_rule") is True
            and (_as_float(best_metrics.get("precision")) or 0.0) >= 0.8
            and (_as_float(best_metrics.get("recall")) or 0.0) >= 0.8
            and all(report_phrases.values())
        ),
    }


def _selector_rule_family_train_holdout_metrics(
    summary_path: Path,
    report_path: Path,
    *,
    expected_row_count: int = 280,
    expected_task_count_filter: int | None = None,
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    holdouts = summary.get("holdout_summaries", {})
    context = holdouts.get("context_hash", {})
    instance = holdouts.get("instance", {})
    dataset = holdouts.get("impact_dataset", {})
    context_micro = context.get("micro", {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "title": "Selector Rule-Family Train-Holdout" in report_text,
        "current": "selector_rule_family_train_holdout = current" in report_text,
        "task_count_filter": (
            f"task_count_filter = {expected_task_count_filter}" in report_text
        ),
        "production_false": "production_validated_selector = false" in report_text,
        "context_material": "context_hash" in report_text
        and "material_passing_fold_count" in report_text,
        "calibration_only": "calibration-only" in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "row_count": _as_int(summary.get("row_count")),
        "context_fold_count": _as_int(context.get("fold_count")),
        "context_material_passing_fold_count": _as_int(
            context.get("material_passing_fold_count")
        ),
        "context_strict_passing_fold_count": _as_int(
            context.get("strict_passing_fold_count")
        ),
        "context_micro_precision": _as_float(context_micro.get("precision")),
        "context_micro_recall": _as_float(context_micro.get("recall")),
        "instance_material_passing_fold_count": _as_int(
            instance.get("material_passing_fold_count")
        ),
        "instance_fold_count": _as_int(instance.get("fold_count")),
        "dataset_material_passing_fold_count": _as_int(
            dataset.get("material_passing_fold_count")
        ),
        "dataset_fold_count": _as_int(dataset.get("fold_count")),
        "report_phrase_presence": report_phrases,
        "check_train_holdout_rule_family_not_context_stable": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("feature_scope") == "addition_before_only"
            and summary.get("row_filter", {}).get("task_count")
            == expected_task_count_filter
            and _as_int(summary.get("row_count")) == expected_row_count
            and checks.get("row_scope_matches_filter") is True
            and checks.get("has_label_mixture") is True
            and checks.get("no_all_holdout_families_material_pass") is True
            and checks.get("context_train_holdout_not_all_material") is True
            and _as_int(context.get("material_passing_fold_count"))
            < _as_int(context.get("fold_count"))
            and all(report_phrases.values())
        ),
    }


def _selector_context_fold_anatomy_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    all_rows = summary.get("all_rows", {})
    twenty = summary.get("twenty_only", {})
    twenty_counts = dict(twenty.get("context_failure_kind_counts", {}) or {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "title": "Selector Context Fold Anatomy" in report_text,
        "current": "selector_context_fold_anatomy = current" in report_text,
        "all_context_folds": "all_context_material_passing_folds = 17/28"
        in report_text,
        "twenty_context_folds": "twenty_context_material_passing_folds = 17/27"
        in report_text,
        "false_positive_kind": "false_positive_no_positive_context" in report_text,
        "missed_positive_kind": "missed_positive_context" in report_text,
        "production_false": "production_validated_selector = false" in report_text,
        "rmp_context": "context/RMP trajectory" in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "all_context_material_passing_fold_count": _as_int(
            all_rows.get("context_material_passing_fold_count")
        ),
        "all_context_fold_count": _as_int(all_rows.get("context_fold_count")),
        "twenty_context_material_passing_fold_count": _as_int(
            twenty.get("context_material_passing_fold_count")
        ),
        "twenty_context_fold_count": _as_int(twenty.get("context_fold_count")),
        "twenty_false_positive_no_positive_context_count": _as_int(
            twenty_counts.get("false_positive_no_positive_context")
        ),
        "twenty_missed_positive_context_count": _as_int(
            twenty_counts.get("missed_positive_context")
        ),
        "twenty_mixed_failure_context_count": _as_int(
            twenty_counts.get("mixed_low_precision_or_recall_context")
        ),
        "twenty_low_positive_context_count": _as_int(
            twenty.get("low_positive_context_count")
        ),
        "twenty_high_positive_context_count": _as_int(
            twenty.get("high_positive_context_count")
        ),
        "report_phrase_presence": report_phrases,
        "check_context_fold_anatomy_supports_context_trajectory_root_cause": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and checks.get("all_rows_context_has_failures") is True
            and checks.get("twenty_only_context_has_failures") is True
            and checks.get("twenty_only_failure_not_from_small_instance") is True
            and checks.get("has_false_positive_no_positive_contexts") is True
            and checks.get("has_missed_positive_contexts") is True
            and checks.get("context_rate_extremes_present") is True
            and _as_int(twenty.get("context_material_passing_fold_count")) == 17
            and _as_int(twenty.get("context_fold_count")) == 27
            and _as_int(twenty_counts.get("false_positive_no_positive_context")) > 0
            and _as_int(twenty_counts.get("missed_positive_context")) > 0
            and all(report_phrases.values())
        ),
    }


def _selector_context_feature_anatomy_metrics(
    summary_path: Path, report_path: Path
) -> dict[str, Any]:
    summary = _read_json(summary_path) if summary_path.exists() else {}
    checks = summary.get("checks", {})
    failure_counts = dict(summary.get("failure_kind_counts", {}) or {})
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    report_phrases = {
        "title": "Selector Context Feature Anatomy" in report_text,
        "current": "selector_context_feature_anatomy = current" in report_text,
        "mixed_instance": (
            f"mixed_instance_group_count = {summary.get('mixed_instance_group_count')}"
            in report_text
        ),
        "mixed_dataset": (
            f"mixed_dataset_group_count = {summary.get('mixed_dataset_group_count')}"
            in report_text
        ),
        "false_positive_kind": "false_positive_no_positive_context" in report_text,
        "missed_positive_kind": "missed_positive_context" in report_text,
        "production_false": "production_validated_selector = false" in report_text,
        "rmp_context": "context/RMP trajectory" in report_text,
    }
    return {
        "source": str(summary_path),
        "report": str(report_path),
        "summary_exists": summary_path.exists(),
        "report_exists": report_path.exists(),
        "row_count": _as_int(summary.get("row_count")),
        "context_count": _as_int(summary.get("context_count")),
        "low_positive_context_count": _as_int(
            summary.get("low_positive_context_count")
        ),
        "high_positive_context_count": _as_int(
            summary.get("high_positive_context_count")
        ),
        "mixed_instance_group_count": _as_int(
            summary.get("mixed_instance_group_count")
        ),
        "mixed_dataset_group_count": _as_int(
            summary.get("mixed_dataset_group_count")
        ),
        "false_positive_no_positive_context_count": _as_int(
            failure_counts.get("false_positive_no_positive_context")
        ),
        "missed_positive_context_count": _as_int(
            failure_counts.get("missed_positive_context")
        ),
        "mixed_low_precision_or_recall_context_count": _as_int(
            failure_counts.get("mixed_low_precision_or_recall_context")
        ),
        "report_phrase_presence": report_phrases,
        "check_context_feature_anatomy_supports_context_root_cause": bool(
            summary_path.exists()
            and report_path.exists()
            and summary.get("all_checks_pass") is True
            and summary.get("schema_version") == "selector_context_feature_anatomy_v1"
            and _as_int(summary.get("row_count")) == 279
            and _as_int(summary.get("context_count")) == 27
            and _as_int(summary.get("mixed_instance_group_count")) > 0
            and _as_int(summary.get("mixed_dataset_group_count")) > 0
            and _as_int(failure_counts.get("false_positive_no_positive_context")) > 0
            and _as_int(failure_counts.get("missed_positive_context")) > 0
            and checks.get("has_twenty_rows") is True
            and checks.get("has_low_and_high_contexts") is True
            and checks.get("same_instance_has_low_and_high_contexts") is True
            and checks.get("same_dataset_has_low_and_high_contexts") is True
            and checks.get("has_false_positive_and_missed_positive_failures")
            is True
            and all(report_phrases.values())
        ),
    }


def _worker_or_audit_triggered(row: dict[str, str]) -> bool:
    bool_keys = (
        "worker_triggered",
        "pulse_worker_trigger",
        "pulse_worker_current_probe_signal",
        "pulse_worker_previous_audit_signal",
        "pulse_audit_trigger",
    )
    if any(_as_bool(row.get(key)) for key in bool_keys):
        return True
    count_keys = ("worker_events", "audit_events", "hidden_negative_audit_events")
    if any(_as_int(row.get(key)) > 0 for key in count_keys):
        return True
    status = str(row.get("pulse_worker_status") or row.get("pulse_audit_status") or "")
    return bool(status and status not in {"SKIPPED", "NOT_RUN"})


def _regex_int(text: str, pattern: str) -> int | None:
    match = re.search(pattern, text, flags=re.MULTILINE | re.DOTALL)
    if not match:
        return None
    return int(match.group(1))


def _small_scale_report_metrics(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    triggered_section = text.split("### 真实触发 worker/audit 的小规模 rows", 1)[-1]
    triggered_section = triggered_section.split("### 没有触发 worker/audit 的小规模 rows", 1)[0]
    nontriggered_section = text.split("### 没有触发 worker/audit 的小规模 rows", 1)[-1]
    nontriggered_section = nontriggered_section.split("## Task 5 / Task 10 拆分", 1)[0]
    metrics = {
        "source": str(path),
        "datasets": _regex_int(text, r"datasets = (\d+)"),
        "nonbaseline_small_rows": _regex_int(text, r"nonbaseline small rows = (\d+)"),
        "triggered_rows": _regex_int(triggered_section, r"rows = (\d+)"),
        "triggered_worsened": _regex_int(triggered_section, r"worsened = (\d+)"),
        "triggered_improved": _regex_int(triggered_section, r"improved = (\d+)"),
        "triggered_worse_count": _regex_int(triggered_section, r"worse_count = (\d+)"),
        "triggered_better_count": _regex_int(triggered_section, r"better_count = (\d+)"),
        "nontriggered_rows": _regex_int(nontriggered_section, r"rows = (\d+)"),
        "nontriggered_worsened": _regex_int(nontriggered_section, r"worsened = (\d+)"),
        "nontriggered_official_changed": _regex_int(
            nontriggered_section, r"official_changed = (\d+)"
        ),
    }
    metrics["check_triggered_all_worse"] = (
        metrics["triggered_rows"] == 220
        and metrics["triggered_worse_count"] == 220
        and metrics["triggered_better_count"] == 0
        and metrics["triggered_improved"] == 0
    )
    metrics["check_nontriggered_no_official_change"] = (
        metrics["nontriggered_rows"] == 325
        and metrics["nontriggered_worsened"] == 0
        and metrics["nontriggered_official_changed"] == 0
    )
    return metrics


def _current_small_summary_scan_metrics(results_dir: Path) -> dict[str, Any]:
    rows: list[tuple[str, dict[str, str]]] = []
    for path in sorted(results_dir.glob("*/summary.csv")):
        try:
            csv_rows = _read_csv(path)
        except (OSError, csv.Error):
            continue
        if not csv_rows:
            continue
        for row in csv_rows:
            scale = str(row.get("scale") or row.get("tasks") or "")
            if scale not in {"5", "10"}:
                continue
            if str(row.get("profile") or "") == "baseline":
                continue
            if not row.get("improvement_class"):
                continue
            rows.append((path.parent.name, row))
    triggered = [row for _, row in rows if _worker_or_audit_triggered(row)]
    nontriggered = [row for _, row in rows if not _worker_or_audit_triggered(row)]

    def summarize(local_rows: list[dict[str, str]]) -> dict[str, int]:
        return {
            "rows": len(local_rows),
            "worsened": sum(
                1 for row in local_rows if row.get("improvement_class") == "worsened"
            ),
            "no_regression": sum(
                1
                for row in local_rows
                if row.get("improvement_class") == "no_regression"
            ),
            "improved": sum(
                1 for row in local_rows if row.get("improvement_class") == "improved"
            ),
            "official_changed": sum(
                1
                for row in local_rows
                if _as_bool(row.get("official_result_changed_vs_baseline"))
            ),
        }

    task5_rows = [
        row for _, row in rows if str(row.get("scale") or row.get("tasks") or "") == "5"
    ]
    task10_rows = [
        row for _, row in rows if str(row.get("scale") or row.get("tasks") or "") == "10"
    ]
    task5_triggered = [row for row in task5_rows if _worker_or_audit_triggered(row)]
    task5_nontriggered = [
        row for row in task5_rows if not _worker_or_audit_triggered(row)
    ]
    task10_triggered = [row for row in task10_rows if _worker_or_audit_triggered(row)]
    task10_nontriggered = [
        row for row in task10_rows if not _worker_or_audit_triggered(row)
    ]
    task5_triggered_summary = summarize(task5_triggered)
    task5_nontriggered_summary = summarize(task5_nontriggered)
    task10_triggered_summary = summarize(task10_triggered)
    task10_nontriggered_summary = summarize(task10_nontriggered)
    metrics = {
        "source": str(results_dir),
        "summary_dirs": len({dataset for dataset, _ in rows}),
        "rows": len(rows),
        "triggered_rows": len(triggered),
        "triggered_worsened": sum(
            1 for row in triggered if row.get("improvement_class") == "worsened"
        ),
        "triggered_no_regression": sum(
            1 for row in triggered if row.get("improvement_class") == "no_regression"
        ),
        "triggered_improved": sum(
            1 for row in triggered if row.get("improvement_class") == "improved"
        ),
        "triggered_official_changed": sum(
            1 for row in triggered if _as_bool(row.get("official_result_changed_vs_baseline"))
        ),
        "nontriggered_rows": len(nontriggered),
        "nontriggered_worsened": sum(
            1 for row in nontriggered if row.get("improvement_class") == "worsened"
        ),
        "nontriggered_improved": sum(
            1 for row in nontriggered if row.get("improvement_class") == "improved"
        ),
        "nontriggered_official_changed": sum(
            1
            for row in nontriggered
            if _as_bool(row.get("official_result_changed_vs_baseline"))
        ),
        "task5_triggered": task5_triggered_summary,
        "task5_nontriggered": task5_nontriggered_summary,
        "task10_triggered": task10_triggered_summary,
        "task10_nontriggered": task10_nontriggered_summary,
    }
    metrics["check_current_scan_same_direction"] = (
        metrics["rows"] >= 545
        and metrics["triggered_rows"] >= 220
        and metrics["triggered_improved"] == 0
        and metrics["triggered_worsened"] > 0
        and metrics["nontriggered_official_changed"] == 0
        and metrics["nontriggered_worsened"] == 0
    )
    metrics["check_task5_noop_guard_no_official_change"] = (
        task5_nontriggered_summary["rows"] > 0
        and task5_nontriggered_summary["worsened"] == 0
        and task5_nontriggered_summary["official_changed"] == 0
    )
    metrics["check_task10_noop_guard_no_official_change"] = (
        task10_nontriggered_summary["rows"] > 0
        and task10_nontriggered_summary["worsened"] == 0
        and task10_nontriggered_summary["official_changed"] == 0
    )
    metrics["check_task10_triggered_is_regression_risk"] = (
        task10_triggered_summary["rows"] > 0
        and task10_triggered_summary["worsened"] > 0
        and task10_triggered_summary["official_changed"] > 0
        and task10_triggered_summary["improved"] == 0
    )
    return metrics


def _phase7o_metrics(path: Path) -> dict[str, Any]:
    rows = _read_csv(path)
    metrics = {
        "source": str(path),
        "rows": len(rows),
        "all_time_limit": all(row.get("official_status") == "TIME_LIMIT" for row in rows),
        "all_incomplete_limit": all(
            row.get("official_pricing_state") == "INCOMPLETE_LIMIT" for row in rows
        ),
        "critical_disagreement_count": sum(
            1 for row in rows if _as_bool(row.get("critical_disagreement"))
        ),
        "worker_events": sum(_as_int(row.get("worker_events")) for row in rows),
        "legacy_final_judge_calls": sum(
            _as_int(row.get("legacy_final_judge_calls")) for row in rows
        ),
        "completion_bound_retry_count": sum(
            _as_int(row.get("completion_bound_retry_count")) for row in rows
        ),
        "pulse_worker_returned_journeys": sum(
            _as_int(row.get("pulse_worker_returned_journeys")) for row in rows
        ),
        "pulse_worker_added_journeys": sum(
            _as_int(row.get("pulse_worker_added_journeys")) for row in rows
        ),
    }
    metrics["check_worker_no_stable_roi"] = (
        metrics["rows"] == 24
        and metrics["all_time_limit"]
        and metrics["all_incomplete_limit"]
        and metrics["critical_disagreement_count"] == 0
        and metrics["worker_events"] == 14
        and metrics["legacy_final_judge_calls"] == 48
        and metrics["completion_bound_retry_count"] == 0
    )
    return metrics


def _phase8q_metrics(path: Path) -> dict[str, Any]:
    rows = _read_csv(path)
    metrics = {
        "source": str(path),
        "rows": len(rows),
        "all_time_limit": all(row.get("official_status") == "TIME_LIMIT" for row in rows),
        "critical_disagreement_count": sum(
            1 for row in rows if _as_bool(row.get("critical_disagreement"))
        ),
        "worker_events": sum(_as_int(row.get("worker_events")) for row in rows),
        "pulse_worker_returned_journeys": sum(
            _as_int(row.get("pulse_worker_returned_journeys")) for row in rows
        ),
        "pulse_worker_added_journeys": sum(
            _as_int(row.get("pulse_worker_added_journeys")) for row in rows
        ),
        "pulse_worker_added_new_task_set_count": sum(
            _as_int(row.get("pulse_worker_added_new_task_set_count")) for row in rows
        ),
        "pulse_worker_added_support_changing_count": sum(
            _as_int(row.get("pulse_worker_added_support_changing_count")) for row in rows
        ),
        "completion_bound_retry_count": sum(
            _as_int(row.get("completion_bound_retry_count")) for row in rows
        ),
    }
    metrics["check_worker_can_add_but_not_solve"] = (
        metrics["rows"] == 35
        and metrics["all_time_limit"]
        and metrics["critical_disagreement_count"] == 0
        and metrics["pulse_worker_returned_journeys"] == 10
        and metrics["pulse_worker_added_journeys"] == 10
        and metrics["pulse_worker_added_new_task_set_count"] == 8
        and metrics["pulse_worker_added_support_changing_count"] == 2
    )
    return metrics


def _candidate_summary_metrics(path: Path) -> dict[str, Any]:
    summary = json.loads(path.read_text(encoding="utf-8"))
    candidate = summary["candidate_summary"]
    single = candidate["twenty_strict_candidate_leave_one_dataset_validation"]
    two = candidate["twenty_strict_candidate_two_feature_leave_one_dataset_validation"]
    instance_single = candidate["twenty_strict_candidate_leave_one_instance_validation"]
    instance_two = candidate["twenty_strict_candidate_two_feature_leave_one_instance_validation"]
    phase10h_rules = [
        rule for rule in two["rules"] if "phase10h" in str(rule.get("held_out", ""))
    ]
    other_rules = [
        rule for rule in two["rules"] if "phase10h" not in str(rule.get("held_out", ""))
    ]
    metrics = {
        "source": str(path),
        "stage_rows": summary["stage_rows"],
        "twenty_strict_stage_rows": summary["twenty_strict_stage_rows"],
        "candidate_rows": candidate["candidate_rows"],
        "twenty_candidate_rows": candidate["twenty_candidate_rows"],
        "twenty_strict_candidate_rows": candidate["twenty_strict_candidate_rows"],
        "twenty_strict_candidate_label_counts": candidate[
            "twenty_strict_candidate_label_counts"
        ],
        "single_threshold": {
            key: single[key] for key in ("total", "accuracy", "tp", "fp", "tn", "fn")
        },
        "two_feature": {
            key: two[key]
            for key in ("total", "accuracy", "precision", "recall", "tp", "fp", "tn", "fn")
        },
        "leave_one_instance_single_threshold": {
            key: instance_single[key]
            for key in ("total", "accuracy", "tp", "fp", "tn", "fn")
        },
        "leave_one_instance_two_feature": {
            key: instance_two[key]
            for key in ("total", "accuracy", "precision", "recall", "tp", "fp", "tn", "fn")
        },
        "two_feature_phase10h_tp": sum(_as_int(rule.get("tp")) for rule in phase10h_rules),
        "two_feature_phase10h_fp": sum(_as_int(rule.get("fp")) for rule in phase10h_rules),
        "two_feature_other_dataset_tp": sum(_as_int(rule.get("tp")) for rule in other_rules),
    }
    metrics["check_candidate_batch_selector_not_stable"] = (
        metrics["candidate_rows"] == 2096
        and metrics["twenty_strict_candidate_rows"] == 848
        and metrics["single_threshold"]["tp"] == 3
        and metrics["single_threshold"]["fn"] == 550
        and metrics["two_feature"]["tp"] == 427
        and metrics["two_feature_phase10h_tp"] == 427
        and metrics["two_feature_other_dataset_tp"] == 0
        and metrics["leave_one_instance_single_threshold"]["tp"] == 56
        and metrics["leave_one_instance_single_threshold"]["fn"] == 497
        and metrics["leave_one_instance_two_feature"]["tp"] == 213
        and metrics["leave_one_instance_two_feature"]["fn"] == 340
    )
    return metrics


def _candidate_model_metrics(path: Path) -> dict[str, Any]:
    summary = json.loads(path.read_text(encoding="utf-8"))

    def compact(group_name: str) -> dict[str, Any]:
        group = summary[group_name]
        models = {
            model_name: {
                key: model[key]
                for key in ("total", "accuracy", "precision", "recall", "tp", "fp", "tn", "fn")
            }
            for model_name, model in group["models"].items()
        }
        passing = {
            model_name: model
            for model_name, model in models.items()
            if (model.get("precision") or 0.0) >= 0.75 and (model.get("recall") or 0.0) >= 0.5
        }
        return {
            "models": models,
            "strict_selector_gate": {
                "precision_min": 0.75,
                "recall_min": 0.5,
                "passing_models": sorted(passing),
            },
        }

    metrics = {
        "source": str(path),
        "rows": summary["rows"],
        "label_counts": summary["label_counts"],
        "leave_one_dataset": compact("leave_one_dataset"),
        "leave_one_instance": compact("leave_one_instance"),
    }
    metrics["check_no_simple_model_passes_strict_gate"] = (
        metrics["rows"] == 848
        and not metrics["leave_one_dataset"]["strict_selector_gate"]["passing_models"]
        and not metrics["leave_one_instance"]["strict_selector_gate"]["passing_models"]
    )
    return metrics


def _selector_failure_metrics(path: Path) -> dict[str, Any]:
    summary = json.loads(path.read_text(encoding="utf-8"))
    top = summary["top_positive_dataset"]
    top_effects = summary["top_aggregate_feature_effects"]
    metrics = {
        "source": str(path),
        "rows": summary["rows"],
        "label_counts": summary["label_counts"],
        "top_positive_dataset": top,
        "robust_single_feature_candidates": summary["robust_single_feature_candidates"],
        "mixed_dataset_direction_feature_count": len(
            summary["mixed_dataset_direction_features"]
        ),
        "mixed_instance_direction_feature_count": len(
            summary["mixed_instance_direction_features"]
        ),
        "top_aggregate_feature_effects": top_effects[:5],
        "checks": summary["checks"],
    }
    metrics["check_selector_failure_anatomy_supports_root_cause"] = (
        metrics["rows"] == 848
        and (top.get("positive_share") or 0.0) >= 0.85
        and not metrics["robust_single_feature_candidates"]
        and metrics["mixed_dataset_direction_feature_count"] > 0
        and metrics["mixed_instance_direction_feature_count"] > 0
        and metrics["checks"]["positive_labels_concentrated"]
        and metrics["checks"]["no_robust_single_feature"]
        and metrics["checks"]["dataset_direction_instability_present"]
        and metrics["checks"]["instance_direction_instability_present"]
    )
    return metrics


def _hindsight_oracle_gap_metrics(path: Path) -> dict[str, Any]:
    summary = json.loads(path.read_text(encoding="utf-8"))
    addition_lod = summary["leave_one_dataset"]["addition_before"]["metrics"]
    hindsight_lod = summary["leave_one_dataset"]["hindsight_trajectory"]["metrics"]
    addition_loi = summary["leave_one_instance"]["addition_before"]["metrics"]
    hindsight_loi = summary["leave_one_instance"]["hindsight_trajectory"]["metrics"]
    top_addition = summary["addition_before_feature_stats"][0]
    top_hindsight = summary["hindsight_feature_stats"][0]
    metrics = {
        "source": str(path),
        "rows": summary["rows"],
        "label_counts": summary["label_counts"],
        "top_addition_before_feature": top_addition,
        "top_hindsight_feature": top_hindsight,
        "leave_one_dataset": {
            "addition_before": {
                key: addition_lod[key]
                for key in ("total", "accuracy", "precision", "recall", "tp", "fp", "tn", "fn")
            },
            "hindsight_trajectory": {
                key: hindsight_lod[key]
                for key in ("total", "accuracy", "precision", "recall", "tp", "fp", "tn", "fn")
            },
        },
        "leave_one_instance": {
            "addition_before": {
                key: addition_loi[key]
                for key in ("total", "accuracy", "precision", "recall", "tp", "fp", "tn", "fn")
            },
            "hindsight_trajectory": {
                key: hindsight_loi[key]
                for key in ("total", "accuracy", "precision", "recall", "tp", "fp", "tn", "fn")
            },
        },
        "checks": summary["checks"],
    }
    metrics["check_hindsight_oracle_gap_supports_root_cause"] = (
        metrics["rows"] == 848
        and top_hindsight["feature"] == "incumbent_within2"
        and (top_hindsight["auc_positive_higher"] or 0.0) > 0.75
        and (top_addition["auc_positive_higher"] or 0.0) < (
            top_hindsight["auc_positive_higher"] or 0.0
        )
        and (hindsight_lod["precision"] or 0.0) > (addition_lod["precision"] or 0.0)
        and _as_int(hindsight_lod["fp"]) < _as_int(addition_lod["fp"])
        and (hindsight_loi["recall"] or 0.0) > (addition_loi["recall"] or 0.0)
        and summary["checks"]["hindsight_has_stronger_aggregate_signal"]
        and summary["checks"]["incumbent_or_zero_fractional_is_top_signal"]
    )
    return metrics


def _candidate_label_granularity_metrics(path: Path) -> dict[str, Any]:
    summary = json.loads(path.read_text(encoding="utf-8"))
    metrics = {
        "source": str(path),
        "stage_rows": summary["stage_rows"],
        "candidate_rows": summary["candidate_rows"],
        "candidate_batches": summary["candidate_batches"],
        "stage_label_counts": summary["stage_label_counts"],
        "batch_label_counts": summary["batch_label_counts"],
        "candidate_label_counts": summary["candidate_label_counts"],
        "batch_positive_rate": summary["batch_positive_rate"],
        "candidate_positive_rate": summary["candidate_positive_rate"],
        "positive_rate_shift_candidate_minus_batch": summary[
            "positive_rate_shift_candidate_minus_batch"
        ],
        "label_mixed_candidate_batches": summary["label_mixed_candidate_batches"],
        "expansion_by_label": summary["expansion_by_label"],
        "improved_vs_worsened_avg_candidate_expansion_ratio": summary[
            "improved_vs_worsened_avg_candidate_expansion_ratio"
        ],
        "checks": summary["checks"],
    }
    metrics["check_candidate_labels_are_batch_level_not_causal"] = (
        metrics["stage_rows"] == 288
        and metrics["candidate_rows"] == 848
        and metrics["candidate_batches"] == 288
        and metrics["label_mixed_candidate_batches"] == 0
        and metrics["batch_label_counts"].get("improved") == 136
        and metrics["batch_label_counts"].get("worsened") == 152
        and metrics["candidate_label_counts"].get("improved") == 553
        and metrics["candidate_label_counts"].get("worsened") == 295
        and (metrics["positive_rate_shift_candidate_minus_batch"] or 0.0) > 0.15
        and (
            metrics["improved_vs_worsened_avg_candidate_expansion_ratio"] or 0.0
        )
        > 2.0
        and summary["checks"]["candidate_rows_are_batch_label_expansion"]
        and summary["checks"]["candidate_expansion_changes_label_balance"]
        and summary["checks"]["improved_batches_have_more_returned_candidates"]
        and summary["checks"]["stage_and_candidate_batch_keys_align"]
    )
    return metrics


def _batch_level_selector_metrics(path: Path) -> dict[str, Any]:
    summary = json.loads(path.read_text(encoding="utf-8"))
    pre_lod = summary["leave_one_dataset"]["pre_batch"]["metrics"]
    oracle_lod = summary["leave_one_dataset"]["post_addition_or_hindsight"]["metrics"]
    pre_loi = summary["leave_one_instance"]["pre_batch"]["metrics"]
    oracle_loi = summary["leave_one_instance"]["post_addition_or_hindsight"]["metrics"]
    top_pre = summary["pre_batch_feature_stats"][0]
    top_oracle = summary["post_addition_or_hindsight_feature_stats"][0]
    metrics = {
        "source": str(path),
        "rows": summary["rows"],
        "label_counts": summary["label_counts"],
        "top_pre_batch_feature": top_pre,
        "top_post_addition_or_hindsight_feature": top_oracle,
        "leave_one_dataset": {
            "pre_batch": {
                key: pre_lod[key]
                for key in ("total", "accuracy", "precision", "recall", "tp", "fp", "tn", "fn")
            },
            "post_addition_or_hindsight": {
                key: oracle_lod[key]
                for key in ("total", "accuracy", "precision", "recall", "tp", "fp", "tn", "fn")
            },
        },
        "leave_one_instance": {
            "pre_batch": {
                key: pre_loi[key]
                for key in ("total", "accuracy", "precision", "recall", "tp", "fp", "tn", "fn")
            },
            "post_addition_or_hindsight": {
                key: oracle_loi[key]
                for key in ("total", "accuracy", "precision", "recall", "tp", "fp", "tn", "fn")
            },
        },
        "checks": summary["checks"],
    }
    metrics["check_batch_level_selector_still_not_stable"] = (
        metrics["rows"] == 288
        and metrics["label_counts"].get("improved") == 136
        and metrics["label_counts"].get("worsened") == 152
        and top_pre["feature"] == "returned_union_size"
        and (pre_lod["precision"] or 0.0) < 0.5
        and _as_int(pre_lod["fp"]) >= 140
        and (pre_loi["precision"] or 0.0) < 0.5
        and _as_int(pre_loi["fp"]) >= 140
        and (oracle_lod["precision"] or 0.0) > (pre_lod["precision"] or 0.0)
        and summary["checks"]["pre_batch_lod_not_strict_gate"]
        and summary["checks"]["pre_batch_loi_not_strict_gate"]
        and summary["checks"]["oracle_lod_has_higher_precision"]
        and summary["checks"]["top_pre_feature_is_batch_size_related"]
    )
    return metrics


def _trajectory_signal_ladder_metrics(path: Path) -> dict[str, Any]:
    summary = json.loads(path.read_text(encoding="utf-8"))
    layers = summary["layer_summary"]
    pre = layers["pre_batch"]["leave_one_dataset"]
    immediate = layers["immediate_addition"]["leave_one_dataset"]
    hindsight = layers["hindsight_trajectory"]["leave_one_dataset"]
    metrics = {
        "source": str(path),
        "rows": summary["rows"],
        "label_counts": summary["label_counts"],
        "layer_summary": layers,
        "checks": summary["checks"],
    }
    metrics["check_signal_ladder_supports_root_cause"] = (
        metrics["rows"] == 288
        and layers["pre_batch"]["top_feature"]["feature"] == "returned_union_size"
        and layers["immediate_addition"]["top_feature"]["feature"] == "addition_new_count"
        and layers["hindsight_trajectory"]["top_feature"]["feature"] == "incumbent_within2"
        and (pre["precision"] or 0.0) < 0.5
        and (immediate["precision"] or 0.0) < 0.5
        and (hindsight["precision"] or 0.0) > (pre["precision"] or 0.0)
        and (hindsight["precision"] or 0.0) > (immediate["precision"] or 0.0)
        and summary["checks"]["pre_batch_precision_low"]
        and summary["checks"]["immediate_addition_not_enough"]
        and summary["checks"]["hindsight_precision_higher_than_pre"]
        and summary["checks"]["hindsight_precision_higher_than_immediate"]
        and summary["checks"]["pre_and_immediate_top_are_quantity_signals"]
    )
    return metrics


def _batch_gate_stability_metrics(path: Path) -> dict[str, Any]:
    summary = json.loads(path.read_text(encoding="utf-8"))
    pos = summary["positive_trigger_gate"]
    neg = summary["negative_noop_gate"]
    pos_lod = pos["leave_one_dataset"]["metrics"]
    pos_loi = pos["leave_one_instance"]["metrics"]
    neg_lod = neg["leave_one_dataset"]["metrics"]
    neg_loi = neg["leave_one_instance"]["metrics"]
    metrics = {
        "source": str(path),
        "rows": summary["rows"],
        "label_counts": summary["label_counts"],
        "positive_trigger_gate": {
            "top_aggregate_rule": pos["top_aggregate_rules"][0],
            "leave_one_dataset": {
                key: pos_lod[key]
                for key in (
                    "total",
                    "accuracy",
                    "precision",
                    "recall",
                    "predicted_positive",
                    "tp",
                    "fp",
                    "tn",
                    "fn",
                )
            },
            "leave_one_instance": {
                key: pos_loi[key]
                for key in (
                    "total",
                    "accuracy",
                    "precision",
                    "recall",
                    "predicted_positive",
                    "tp",
                    "fp",
                    "tn",
                    "fn",
                )
            },
        },
        "negative_noop_gate": {
            "top_aggregate_rule": neg["top_aggregate_rules"][0],
            "leave_one_dataset": {
                key: neg_lod[key]
                for key in (
                    "total",
                    "accuracy",
                    "precision",
                    "recall",
                    "predicted_positive",
                    "tp",
                    "fp",
                    "tn",
                    "fn",
                )
            },
            "leave_one_instance": {
                key: neg_loi[key]
                for key in (
                    "total",
                    "accuracy",
                    "precision",
                    "recall",
                    "predicted_positive",
                    "tp",
                    "fp",
                    "tn",
                    "fn",
                )
            },
        },
        "checks": summary["checks"],
    }
    pos_top = pos["top_aggregate_rules"][0]
    neg_top = neg["top_aggregate_rules"][0]
    metrics["check_batch_gates_are_not_stable"] = (
        metrics["rows"] == 288
        and pos_top["feature"] == "returned_union_size"
        and pos_top["operator"] == ">="
        and (pos_top["metrics"]["precision"] or 0.0) > 0.8
        and _as_int(pos_lod["tp"]) == 0
        and (pos_loi["precision"] or 0.0) <= 0.2
        and neg_top["feature"] == "returned_union_size"
        and neg_top["operator"] == "<="
        and (neg_top["metrics"]["precision"] or 0.0) > 0.8
        and (neg_lod["precision"] or 0.0) < 0.5
        and (neg_loi["recall"] or 0.0) < 0.05
        and summary["checks"]["positive_gate_overfits"]
        and summary["checks"]["negative_gate_not_viable"]
    )
    return metrics


def _context_stratification_metrics(path: Path) -> dict[str, Any]:
    summary = json.loads(path.read_text(encoding="utf-8"))
    group_summaries = summary["group_summaries"]
    metrics = {
        "source": str(path),
        "rows": summary["rows"],
        "label_counts": summary["label_counts"],
        "group_rate_ranges": {
            key: payload["improved_rate_range"]
            for key, payload in group_summaries.items()
        },
        "mixed_direction_features": {
            key: payload["mixed_direction_features"]
            for key, payload in group_summaries.items()
        },
        "checks": summary["checks"],
    }
    metrics["check_context_stratification_explains_gate_failure"] = (
        metrics["rows"] == 288
        and (metrics["group_rate_ranges"]["dataset"] or 0.0) > 0.7
        and (metrics["group_rate_ranges"]["instance"] or 0.0) > 0.3
        and (metrics["group_rate_ranges"]["profile"] or 0.0) > 0.8
        and "returned_union_size" in metrics["mixed_direction_features"]["dataset"]
        and "returned_union_size" in metrics["mixed_direction_features"]["instance"]
        and "returned_union_size" in metrics["mixed_direction_features"]["profile"]
        and summary["checks"]["dataset_base_rate_heterogeneous"]
        and summary["checks"]["instance_base_rate_heterogeneous"]
        and summary["checks"]["profile_base_rate_heterogeneous"]
        and summary["checks"]["returned_union_size_mixed_by_profile"]
        and summary["checks"]["top_feature_direction_mixed_somewhere"]
    )
    return metrics


def _context_only_baseline_metrics(path: Path) -> dict[str, Any]:
    summary = json.loads(path.read_text(encoding="utf-8"))
    best = summary["best_by_holdout"]
    metrics = {
        "source": str(path),
        "rows": summary["rows"],
        "label_counts": summary["label_counts"],
        "best_by_holdout": best,
        "checks": summary["checks"],
    }
    metrics["check_context_only_has_signal_but_not_enough"] = (
        metrics["rows"] == 288
        and (best["instance"]["metrics"]["precision"] or 0.0) >= 0.6
        and (best["profile"]["metrics"]["precision"] or 0.0) >= 0.6
        and (best["dataset"]["metrics"]["precision"] or 0.0) < 0.6
        and (best["dataset"]["metrics"]["recall"] or 0.0) < 0.5
        and all((payload["metrics"]["precision"] or 0.0) < 0.75 for payload in best.values())
        and summary["checks"]["context_only_has_signal"]
        and summary["checks"]["context_only_not_production_gate"]
        and summary["checks"]["dataset_holdout_context_is_weak"]
    )
    return metrics


def _matched_context_audit_metrics(path: Path) -> dict[str, Any]:
    summary = json.loads(path.read_text(encoding="utf-8"))
    strict = summary["matched_summaries"]["instance_profile"]
    metrics = {
        "source": str(path),
        "rows": summary["rows"],
        "label_counts": summary["label_counts"],
        "strict_instance_profile": {
            key: value
            for key, value in strict.items()
            if key != "mixed_groups"
        },
        "checks": summary["checks"],
    }
    directions = strict["top_direction_counts"]
    metrics["check_matched_context_needs_counterfactual"] = (
        metrics["rows"] == 288
        and strict["mixed_group_count"] == 8
        and strict["mixed_rows"] == 94
        and (strict["mixed_row_share"] or 0.0) < 0.35
        and directions.get("positive", 0) > 0
        and directions.get("negative", 0) > 0
        and max(strict["top_feature_counts"].values() or [0]) < strict["mixed_group_count"]
        and summary["checks"]["strict_matched_context_sparse"]
        and summary["checks"]["strict_top_directions_mixed"]
        and summary["checks"]["strict_no_single_top_feature_dominates"]
        and summary["checks"]["matched_context_requires_counterfactual"]
    )
    return metrics


def _matched_context_pairwise_metrics(path: Path) -> dict[str, Any]:
    summary = json.loads(path.read_text(encoding="utf-8"))
    top = summary["feature_pairwise_stats"][0]
    metrics = {
        "source": str(path),
        "rows": summary["rows"],
        "label_counts": summary["label_counts"],
        "match_keys": summary["match_keys"],
        "mixed_group_count": summary["mixed_group_count"],
        "mixed_rows": summary["mixed_rows"],
        "strict_gate": summary["strict_gate"],
        "passing_strict_pairwise_gate": summary["passing_strict_pairwise_gate"],
        "top_feature": {
            key: top.get(key)
            for key in (
                "feature",
                "pairs",
                "best_orientation_auc",
                "dominant_direction",
                "non_tie_share",
                "group_consistency",
                "group_direction_counts",
            )
        },
        "checks": summary["checks"],
    }
    metrics["check_pairwise_contrast_requires_replay"] = (
        metrics["rows"] == 288
        and metrics["mixed_group_count"] == 8
        and metrics["mixed_rows"] == 94
        and metrics["top_feature"]["pairs"] == 244
        and metrics["top_feature"]["feature"] == "returned_union_size"
        and (metrics["top_feature"]["best_orientation_auc"] or 0.0) < 0.6
        and (metrics["top_feature"]["non_tie_share"] or 0.0) < 0.2
        and metrics["passing_strict_pairwise_gate"] == []
        and summary["checks"]["has_matched_pairs"]
        and summary["checks"]["no_feature_passes_strict_pairwise_gate"]
        and summary["checks"]["top_feature_not_production_stable"]
        and summary["checks"]["pairwise_contrast_requires_replay"]
    )
    return metrics


def _exact_context_label_conflict_metrics(path: Path) -> dict[str, Any]:
    summary = json.loads(path.read_text(encoding="utf-8"))
    exact_context = summary["levels"]["exact_context"]
    full_features = summary["levels"]["exact_context_full_features"]
    metrics = {
        "source": str(path),
        "rows": summary["rows"],
        "label_counts": summary["label_counts"],
        "exact_context": {
            key: value
            for key, value in exact_context.items()
            if key != "conflicts"
        },
        "exact_context_full_features": {
            key: value
            for key, value in full_features.items()
            if key != "conflicts"
        },
        "checks": summary["checks"],
    }
    largest = full_features["largest_conflict"] or {}
    metrics["check_observational_labels_not_causal_for_batch"] = (
        metrics["rows"] == 288
        and exact_context["conflict_group_count"] == 12
        and exact_context["conflict_rows"] == 120
        and full_features["conflict_group_count"] == 14
        and full_features["conflict_rows"] == 65
        and largest.get("rows") == 15
        and largest.get("label_counts", {}).get("improved") == 4
        and largest.get("label_counts", {}).get("worsened") == 11
        and summary["checks"]["exact_context_has_conflicts"]
        and summary["checks"]["full_feature_vectors_have_conflicts"]
        and summary["checks"]["full_feature_conflict_rows_are_material"]
        and summary["checks"]["observational_labels_not_causal_for_batch"]
    )
    return metrics


def _counterfactual_replay_coverage_metrics(path: Path) -> dict[str, Any]:
    summary = json.loads(path.read_text(encoding="utf-8"))
    metrics = {
        "source": str(path),
        "rows": summary["rows"],
        "label_counts": summary["label_counts"],
        "context_keys": summary["context_keys"],
        "descriptor_keys": summary["descriptor_keys"],
        "mixed_context_count": summary["mixed_context_count"],
        "mixed_context_rows": summary["mixed_context_rows"],
        "descriptor_totals_in_mixed_contexts": summary[
            "descriptor_totals_in_mixed_contexts"
        ],
        "pure_descriptor_pair_count": summary["pure_descriptor_pair_count"],
        "replay_candidate_context_count": summary["replay_candidate_context_count"],
        "mixed_descriptor_context_count": summary["mixed_descriptor_context_count"],
        "checks": summary["checks"],
    }
    totals = metrics["descriptor_totals_in_mixed_contexts"]
    metrics["check_existing_replay_is_candidate_only"] = (
        metrics["rows"] == 288
        and metrics["mixed_context_count"] == 12
        and metrics["mixed_context_rows"] == 120
        and totals["pure_improved"] == 12
        and totals["pure_worsened"] == 21
        and totals["mixed"] == 14
        and metrics["pure_descriptor_pair_count"] == 40
        and metrics["replay_candidate_context_count"] == 6
        and metrics["mixed_descriptor_context_count"] == 10
        and summary["checks"]["has_replay_candidates"]
        and summary["checks"]["replay_candidates_are_sparse"]
        and summary["checks"]["mixed_descriptors_remain_common"]
        and summary["checks"]["existing_observational_replay_is_candidate_only"]
    )
    return metrics


def _counterfactual_replay_candidate_metrics(path: Path) -> dict[str, Any]:
    summary = json.loads(path.read_text(encoding="utf-8"))
    recommended = summary["recommended_candidate_ids"]
    metrics = {
        "source": str(path),
        "coverage_summary": summary["coverage_summary"],
        "candidate_count": summary["candidate_count"],
        "low_context_noise_candidate_count": summary[
            "low_context_noise_candidate_count"
        ],
        "mixed_descriptor_context_candidate_count": summary[
            "mixed_descriptor_context_candidate_count"
        ],
        "recommended_candidate_ids": recommended,
        "checks": summary["checks"],
    }
    metrics["check_replay_candidate_manifest_ready"] = (
        metrics["candidate_count"] == 40
        and metrics["low_context_noise_candidate_count"] == 3
        and metrics["mixed_descriptor_context_candidate_count"] == 37
        and recommended == [
            "replay_candidate_001",
            "replay_candidate_003",
            "replay_candidate_004",
        ]
        and summary["checks"]["has_manifest_candidates"]
        and summary["checks"]["has_low_context_noise_candidates"]
        and summary["checks"]["has_mixed_context_stress_candidate"]
        and summary["checks"]["recommended_batch_is_small"]
    )
    return metrics


def _counterfactual_replay_readiness_metrics(path: Path) -> dict[str, Any]:
    summary = json.loads(path.read_text(encoding="utf-8"))
    checks = summary["checks"]
    metrics = {
        "source": str(path),
        "recommended_candidate_count": summary["recommended_candidate_count"],
        "descriptor_count": summary["descriptor_count"],
        "ready_candidate_count": summary["ready_candidate_count"],
        "descriptors_with_truncated_sampling": summary[
            "descriptors_with_truncated_sampling"
        ],
        "descriptors_with_candidate_row_start_times": summary[
            "descriptors_with_candidate_row_start_times"
        ],
        "descriptors_with_ambiguous_candidate_row_start_times": summary[
            "descriptors_with_ambiguous_candidate_row_start_times"
        ],
        "required_replay_fields": summary["required_replay_fields"],
        "checks": checks,
    }
    metrics["check_replay_manifest_not_exact_replay_ready"] = (
        metrics["recommended_candidate_count"] == 3
        and metrics["descriptor_count"] == 6
        and metrics["ready_candidate_count"] == 0
        and metrics["descriptors_with_truncated_sampling"] == 1
        and metrics["descriptors_with_candidate_row_start_times"] == 6
        and metrics["descriptors_with_ambiguous_candidate_row_start_times"] == 0
        and checks["recommended_candidates_present"]
        and checks["no_candidate_ready_for_exact_replay"]
        and checks["manifest_lacks_required_replay_fields"]
        and checks["candidate_rows_are_not_exact_context_snapshots"]
        and checks["needs_new_no_certificate_effect_replay_capture"]
    )
    return metrics


def _counterfactual_replay_materialization_metrics(path: Path) -> dict[str, Any]:
    summary = json.loads(path.read_text(encoding="utf-8"))
    checks = summary["checks"]
    metrics = {
        "source": str(path),
        "recommended_candidate_count": summary["recommended_candidate_count"],
        "descriptor_count": summary["descriptor_count"],
        "entry_count": summary["entry_count"],
        "materialized_entry_count": summary["materialized_entry_count"],
        "observed_descriptors_materialized": summary[
            "observed_descriptors_materialized"
        ],
        "complete_descriptors_materialized": summary[
            "complete_descriptors_materialized"
        ],
        "checks": checks,
    }
    metrics["check_observed_entries_materialize_but_replay_still_partial"] = (
        metrics["recommended_candidate_count"] == 3
        and metrics["descriptor_count"] == 6
        and metrics["entry_count"] == 27
        and metrics["materialized_entry_count"] == 27
        and metrics["observed_descriptors_materialized"] == 6
        and metrics["complete_descriptors_materialized"] == 5
        and checks["recommended_candidates_present"]
        and checks["all_instances_loaded"]
        and checks["all_observed_entries_materialized"]
        and checks["not_all_complete_descriptors_materialized"]
        and checks["still_not_exact_replay_payload"]
    )
    return metrics


def _counterfactual_replay_capture_smoke_metrics(path: Path) -> dict[str, Any]:
    summary = json.loads(path.read_text(encoding="utf-8"))
    issue_counts = dict(summary.get("issue_counts", {}))
    event_count = _as_int(summary.get("event_count"))
    complete_event_count = _as_int(summary.get("complete_event_count"))
    truncated_event_count = _as_int(summary.get("truncated_event_count"))
    returned_journey_count = _as_int(summary.get("returned_journey_count"))
    captured_journey_count = _as_int(summary.get("captured_journey_count"))
    metrics = {
        "source": str(path),
        "event_count": event_count,
        "complete_event_count": complete_event_count,
        "truncated_event_count": truncated_event_count,
        "returned_journey_count": returned_journey_count,
        "captured_journey_count": captured_journey_count,
        "issue_counts": issue_counts,
        "checks": dict(summary.get("checks", {})),
    }
    metrics["check_capture_smoke_replay_payload_ready"] = (
        bool(summary.get("all_checks_pass"))
        and event_count > 0
        and complete_event_count > 0
        and truncated_event_count == 0
        and returned_journey_count == captured_journey_count
        and not issue_counts
    )
    return metrics


def _counterfactual_replay_manifest_smoke_metrics(path: Path) -> dict[str, Any]:
    summary = json.loads(path.read_text(encoding="utf-8"))
    checks = dict(summary.get("checks", {}))
    case_summaries = list(summary.get("case_summaries", []) or [])
    candidate_summary = dict(case_summaries[0].get("candidate_summary", {})) if case_summaries else {}
    metrics = {
        "source": str(path),
        "case_count": _as_int(summary.get("case_count")),
        "ready_case_count": _as_int(summary.get("ready_case_count")),
        "candidate_count": _as_int(summary.get("candidate_count")),
        "treatment_count": _as_int(summary.get("treatment_count")),
        "first_case_candidate_summary": candidate_summary,
        "checks": checks,
    }
    metrics["check_replay_manifest_smoke_ready_but_not_optimization_evidence"] = (
        bool(summary.get("all_checks_pass"))
        and metrics["case_count"] > 0
        and metrics["ready_case_count"] > 0
        and metrics["candidate_count"] > 0
        and metrics["treatment_count"] >= 3
        and checks.get("has_ready_rmp_replay_cases") is True
        and checks.get("all_cases_no_certificate_effect") is True
    )
    return metrics


def _counterfactual_replay_feasible_smoke_metrics(path: Path) -> dict[str, Any]:
    summary = json.loads(path.read_text(encoding="utf-8"))
    checks = dict(summary.get("checks", {}))
    case_summaries = list(summary.get("case_summaries", []) or [])
    first_case = dict(case_summaries[0]) if case_summaries else {}
    metrics = {
        "source": str(path),
        "case_count": _as_int(summary.get("case_count")),
        "ready_case_count": _as_int(summary.get("ready_case_count")),
        "changed_treatment_count": _as_int(summary.get("changed_treatment_count")),
        "improving_treatment_count": _as_int(summary.get("improving_treatment_count")),
        "first_case_best_objective_delta": first_case.get("best_objective_delta"),
        "first_case_control": dict(first_case.get("control", {})),
        "checks": checks,
    }
    metrics["check_duplicate_negative_replay_is_noop"] = (
        bool(summary.get("all_checks_pass"))
        and metrics["case_count"] == 1
        and metrics["ready_case_count"] == 1
        and metrics["changed_treatment_count"] == 0
        and metrics["improving_treatment_count"] == 0
        and float(first_case.get("best_objective_delta", 1.0)) == 0.0
        and checks.get("control_rmp_solved") is True
        and checks.get("all_replay_is_no_certificate_effect") is True
    )
    return metrics


def _counterfactual_replay_gap_metrics(path: Path) -> dict[str, Any]:
    summary = json.loads(path.read_text(encoding="utf-8"))
    checks = dict(summary.get("checks", {}))
    metrics = {
        "source": str(path),
        "files_scanned": _as_int(summary.get("files_scanned")),
        "addition_event_count": _as_int(summary.get("addition_event_count")),
        "capture_event_count": _as_int(summary.get("capture_event_count")),
        "replay_candidate_addition_count": _as_int(
            summary.get("replay_candidate_addition_count")
        ),
        "replay_candidate_with_capture_count": _as_int(
            summary.get("replay_candidate_with_capture_count")
        ),
        "missing_capture_replay_candidate_count": _as_int(
            summary.get("missing_capture_replay_candidate_count")
        ),
        "replay_candidate_added_journey_total": _as_int(
            summary.get("replay_candidate_added_journey_total")
        ),
        "replay_candidate_active_changed_task_set_total": _as_int(
            summary.get("replay_candidate_active_changed_task_set_total")
        ),
        "replay_candidate_new_task_set_total": _as_int(
            summary.get("replay_candidate_new_task_set_total")
        ),
        "replay_candidate_replacement_task_set_total": _as_int(
            summary.get("replay_candidate_replacement_task_set_total")
        ),
        "checks": checks,
    }
    metrics["check_real_additions_still_need_capture_for_replay"] = (
        bool(summary.get("all_checks_pass"))
        and metrics["files_scanned"] == 35
        and metrics["replay_candidate_addition_count"] == 136
        and metrics["missing_capture_replay_candidate_count"] == 136
        and metrics["replay_candidate_with_capture_count"] == 0
        and metrics["replay_candidate_added_journey_total"] == 143
        and checks.get("historical_additions_are_not_controlled_replay_ready") is True
    )
    return metrics


def _counterfactual_replay_real_capture_metrics(
    audit_path: Path,
    manifest_path: Path,
    replay_path: Path,
) -> dict[str, Any]:
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    replay = json.loads(replay_path.read_text(encoding="utf-8"))
    manifest_cases = list(manifest.get("case_summaries", []) or [])
    manifest_first = dict(manifest_cases[0]) if manifest_cases else {}
    replay_cases = list(replay.get("case_summaries", []) or [])
    replay_first = dict(replay_cases[0]) if replay_cases else {}
    candidate_summary = dict(manifest_first.get("candidate_summary", {}))
    best_delta = replay_first.get("best_objective_delta")
    try:
        best_delta_value = float(best_delta)
    except (TypeError, ValueError):
        best_delta_value = 0.0
    metrics = {
        "sources": {
            "audit": str(audit_path),
            "manifest": str(manifest_path),
            "replay": str(replay_path),
        },
        "capture_event_count": _as_int(audit.get("event_count")),
        "captured_journey_count": _as_int(audit.get("captured_journey_count")),
        "pool_journey_payload_count": _as_int(audit.get("pool_journey_payload_count")),
        "manifest_case_count": _as_int(manifest.get("case_count")),
        "manifest_ready_case_count": _as_int(manifest.get("ready_case_count")),
        "manifest_candidate_count": _as_int(manifest.get("candidate_count")),
        "manifest_treatment_count": _as_int(manifest.get("treatment_count")),
        "candidate_summary": candidate_summary,
        "replay_case_count": _as_int(replay.get("case_count")),
        "replay_ready_case_count": _as_int(replay.get("ready_case_count")),
        "changed_treatment_count": _as_int(replay.get("changed_treatment_count")),
        "improving_treatment_count": _as_int(replay.get("improving_treatment_count")),
        "best_objective_delta": best_delta,
        "control": dict(replay_first.get("control", {})),
        "checks": {
            "audit": dict(audit.get("checks", {})),
            "manifest": dict(manifest.get("checks", {})),
            "replay": dict(replay.get("checks", {})),
        },
    }
    metrics["check_real_capture_replay_has_local_rmp_impact"] = (
        bool(audit.get("all_checks_pass"))
        and bool(manifest.get("all_checks_pass"))
        and bool(replay.get("all_checks_pass"))
        and metrics["capture_event_count"] == 1
        and metrics["manifest_ready_case_count"] == 1
        and metrics["replay_ready_case_count"] == 1
        and metrics["manifest_candidate_count"] >= 1
        and _as_int(candidate_summary.get("new_task_set_count")) >= 1
        and metrics["changed_treatment_count"] >= 1
        and metrics["improving_treatment_count"] >= 1
        and best_delta_value < -1.0e-9
        and metrics["checks"]["replay"].get("all_replay_is_no_certificate_effect") is True
        and metrics["checks"]["replay"].get("control_rmp_solved") is True
    )
    return metrics


def _counterfactual_replay_impact_dataset_metrics(
    real_capture_path: Path,
    duplicate_noop_path: Path,
    combined_path: Path,
) -> dict[str, Any]:
    real_capture = json.loads(real_capture_path.read_text(encoding="utf-8"))
    duplicate_noop = json.loads(duplicate_noop_path.read_text(encoding="utf-8"))
    combined = json.loads(combined_path.read_text(encoding="utf-8"))
    metrics = {
        "sources": {
            "real_capture": str(real_capture_path),
            "duplicate_noop": str(duplicate_noop_path),
            "combined": str(combined_path),
        },
        "real_capture": {
            "case_count": _as_int(real_capture.get("case_count")),
            "candidate_row_count": _as_int(real_capture.get("candidate_row_count")),
            "single_candidate_with_replay_count": _as_int(
                real_capture.get("single_candidate_with_replay_count")
            ),
            "high_impact_candidate_count": _as_int(
                real_capture.get("high_impact_candidate_count")
            ),
            "noop_candidate_count": _as_int(real_capture.get("noop_candidate_count")),
            "unknown_candidate_count": _as_int(
                real_capture.get("unknown_candidate_count")
            ),
            "control_unsolved_case_count": _as_int(
                real_capture.get("control_unsolved_case_count")
            ),
            "full_batch_improved_count": _as_int(
                real_capture.get("full_batch_improved_count")
            ),
            "best_objective_delta": real_capture.get("best_objective_delta"),
            "checks": dict(real_capture.get("checks", {})),
        },
        "duplicate_noop": {
            "case_count": _as_int(duplicate_noop.get("case_count")),
            "candidate_row_count": _as_int(duplicate_noop.get("candidate_row_count")),
            "single_candidate_with_replay_count": _as_int(
                duplicate_noop.get("single_candidate_with_replay_count")
            ),
            "high_impact_candidate_count": _as_int(
                duplicate_noop.get("high_impact_candidate_count")
            ),
            "noop_candidate_count": _as_int(duplicate_noop.get("noop_candidate_count")),
            "unknown_candidate_count": _as_int(
                duplicate_noop.get("unknown_candidate_count")
            ),
            "control_unsolved_case_count": _as_int(
                duplicate_noop.get("control_unsolved_case_count")
            ),
            "full_batch_improved_count": _as_int(
                duplicate_noop.get("full_batch_improved_count")
            ),
            "best_objective_delta": duplicate_noop.get("best_objective_delta"),
            "checks": dict(duplicate_noop.get("checks", {})),
        },
        "combined": {
            "dataset_count": _as_int(combined.get("dataset_count")),
            "candidate_row_count": _as_int(combined.get("candidate_row_count")),
            "high_impact_candidate_count": _as_int(
                combined.get("high_impact_candidate_count")
            ),
            "noop_candidate_count": _as_int(combined.get("noop_candidate_count")),
            "best_objective_delta": combined.get("best_objective_delta"),
            "candidate_impact_class_counts": dict(
                combined.get("candidate_impact_class_counts", {})
            ),
            "treatment_impact_class_counts": dict(
                combined.get("treatment_impact_class_counts", {})
            ),
            "checks": dict(combined.get("checks", {})),
        },
    }
    real_delta = metrics["real_capture"]["best_objective_delta"]
    duplicate_delta = metrics["duplicate_noop"]["best_objective_delta"]
    try:
        real_delta_value = float(real_delta)
    except (TypeError, ValueError):
        real_delta_value = 0.0
    try:
        duplicate_delta_value = float(duplicate_delta)
    except (TypeError, ValueError):
        duplicate_delta_value = 1.0
    metrics["check_impact_dataset_separates_high_impact_and_noop"] = (
        bool(real_capture.get("all_checks_pass"))
        and bool(duplicate_noop.get("all_checks_pass"))
        and metrics["real_capture"]["candidate_row_count"] == 4
        and metrics["real_capture"]["single_candidate_with_replay_count"] == 4
        and metrics["real_capture"]["high_impact_candidate_count"] == 4
        and metrics["real_capture"]["noop_candidate_count"] == 0
        and metrics["real_capture"]["unknown_candidate_count"] == 0
        and metrics["real_capture"]["control_unsolved_case_count"] == 0
        and metrics["real_capture"]["full_batch_improved_count"] == 1
        and real_delta_value < -1.0e-9
        and metrics["duplicate_noop"]["candidate_row_count"] == 1
        and metrics["duplicate_noop"]["single_candidate_with_replay_count"] == 1
        and metrics["duplicate_noop"]["high_impact_candidate_count"] == 0
        and metrics["duplicate_noop"]["noop_candidate_count"] == 1
        and metrics["duplicate_noop"]["unknown_candidate_count"] == 0
        and metrics["duplicate_noop"]["control_unsolved_case_count"] == 0
        and metrics["duplicate_noop"]["full_batch_improved_count"] == 0
        and duplicate_delta_value == 0.0
        and bool(combined.get("all_checks_pass"))
        and metrics["combined"]["dataset_count"] == 5
        and metrics["combined"]["candidate_row_count"] == 280
        and metrics["combined"]["high_impact_candidate_count"] == 209
        and metrics["combined"]["noop_candidate_count"] == 71
        and metrics["combined"]["checks"].get("has_high_impact_and_noop_examples") is True
        and metrics["real_capture"]["checks"].get("all_replay_controls_solved") is True
        and metrics["real_capture"]["checks"].get("all_single_candidates_have_finite_delta") is True
        and metrics["duplicate_noop"]["checks"].get("all_replay_controls_solved") is True
        and metrics["duplicate_noop"]["checks"].get("all_single_candidates_have_finite_delta") is True
        and metrics["real_capture"]["checks"].get("replay_is_no_certificate_effect") is True
        and metrics["duplicate_noop"]["checks"].get("replay_is_no_certificate_effect") is True
    )
    return metrics


def _counterfactual_replay_payload_quality_metrics(
    report_path: Path,
    audit_path: Path,
    manifest_path: Path,
    replay_path: Path,
    impact_path: Path,
) -> dict[str, Any]:
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    replay = json.loads(replay_path.read_text(encoding="utf-8"))
    impact = json.loads(impact_path.read_text(encoding="utf-8"))
    metrics = {
        "sources": {
            "report": str(report_path),
            "audit": str(audit_path),
            "manifest": str(manifest_path),
            "replay": str(replay_path),
            "impact": str(impact_path),
        },
        "report_exists": report_path.exists(),
        "audit_event_count": _as_int(audit.get("event_count")),
        "audit_captured_journey_count": _as_int(audit.get("captured_journey_count")),
        "manifest_case_count": _as_int(manifest.get("case_count")),
        "manifest_ready_case_count": _as_int(manifest.get("ready_case_count")),
        "manifest_candidate_count": _as_int(manifest.get("candidate_count")),
        "replay_all_checks_pass": bool(replay.get("all_checks_pass")),
        "replay_ready_case_count": _as_int(replay.get("ready_case_count")),
        "replay_changed_treatment_count": _as_int(replay.get("changed_treatment_count")),
        "replay_improving_treatment_count": _as_int(
            replay.get("improving_treatment_count")
        ),
        "replay_control_rmp_solved": bool(
            (replay.get("checks") or {}).get("control_rmp_solved")
        ),
        "impact_all_checks_pass": bool(impact.get("all_checks_pass")),
        "impact_candidate_row_count": _as_int(impact.get("candidate_row_count")),
        "impact_unknown_candidate_count": _as_int(impact.get("unknown_candidate_count")),
        "impact_control_unsolved_case_count": _as_int(
            impact.get("control_unsolved_case_count")
        ),
        "impact_high_impact_candidate_count": _as_int(
            impact.get("high_impact_candidate_count")
        ),
    }
    metrics["check_payload_quality_guard_rejects_unsolved_control"] = (
        metrics["report_exists"]
        and bool(audit.get("all_checks_pass"))
        and bool(manifest.get("all_checks_pass"))
        and metrics["audit_event_count"] == 2
        and metrics["audit_captured_journey_count"] == 7
        and metrics["manifest_case_count"] == 2
        and metrics["manifest_ready_case_count"] == 1
        and metrics["manifest_candidate_count"] == 7
        and metrics["replay_all_checks_pass"] is False
        and metrics["replay_control_rmp_solved"] is True
        and metrics["replay_ready_case_count"] == 1
        and metrics["impact_all_checks_pass"] is False
        and metrics["impact_candidate_row_count"] == 7
        and metrics["impact_high_impact_candidate_count"] == 4
        and metrics["impact_unknown_candidate_count"] == 0
        and metrics["impact_control_unsolved_case_count"] == 1
    )
    return metrics


def _counterfactual_replay_capture_expansion_metrics(
    mt20_tranq_summary_path: Path,
    mt20_tranq_audit_path: Path,
    tranq20_summary_path: Path,
    tranq20_audit_path: Path,
) -> dict[str, Any]:
    def load_run(summary_path: Path, audit_path: Path) -> dict[str, Any]:
        rows = json.loads(summary_path.read_text(encoding="utf-8"))
        row = dict(rows[0]) if isinstance(rows, list) and rows else {}
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        return {
            "source": str(summary_path),
            "audit_source": str(audit_path),
            "instance": str(row.get("instance", "")),
            "status": str(row.get("status", "")),
            "pricing_state": str(row.get("pricing_state", "")),
            "official_best_rc": row.get("official_best_rc"),
            "worker_events": _as_int(row.get("worker_events")),
            "worker_triggered": bool(row.get("worker_triggered")),
            "worker_returned_journeys": _as_int(row.get("worker_returned_journeys")),
            "worker_added_journeys": _as_int(row.get("worker_added_journeys")),
            "profile_dp_tail_class": str(row.get("profile_dp_tail_class", "")),
            "profile_dp_tail_reason": str(row.get("profile_dp_tail_reason", "")),
            "capture_event_count": _as_int(audit.get("event_count")),
            "captured_journey_count": _as_int(audit.get("captured_journey_count")),
            "has_capture_events": bool((audit.get("checks") or {}).get("has_capture_events")),
            "audit_all_checks_pass": bool(audit.get("all_checks_pass")),
        }

    mt20_tranq = load_run(mt20_tranq_summary_path, mt20_tranq_audit_path)
    tranq20 = load_run(tranq20_summary_path, tranq20_audit_path)
    runs = [mt20_tranq, tranq20]
    metrics = {
        "sources": {
            "mt20_tranq_summary": str(mt20_tranq_summary_path),
            "mt20_tranq_audit": str(mt20_tranq_audit_path),
            "tranq20_summary": str(tranq20_summary_path),
            "tranq20_audit": str(tranq20_audit_path),
        },
        "runs": runs,
        "run_count": len(runs),
        "worker_event_count": sum(_as_int(item["worker_events"]) for item in runs),
        "capture_event_count": sum(_as_int(item["capture_event_count"]) for item in runs),
        "captured_journey_count": sum(_as_int(item["captured_journey_count"]) for item in runs),
        "state_cap_tail_count": sum(
            1 for item in runs if item["profile_dp_tail_class"] == "profile_dp_state_cap_tail"
        ),
    }
    metrics["check_capture_expansion_confirms_unstable_capture"] = (
        metrics["run_count"] == 2
        and all(item["status"] == "TIME_LIMIT" for item in runs)
        and all(item["pricing_state"] == "INCOMPLETE_LIMIT" for item in runs)
        and metrics["worker_event_count"] == 0
        and metrics["capture_event_count"] == 0
        and metrics["captured_journey_count"] == 0
        and metrics["state_cap_tail_count"] == 2
        and not any(item["has_capture_events"] for item in runs)
    )
    return metrics


def _counterfactual_replay_global_capture_scan_metrics(
    report_path: Path,
    audit_path: Path,
    manifest_path: Path,
    manifest_summary_path: Path,
    replay_summary_path: Path,
    impact_path: Path,
) -> dict[str, Any]:
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_summary = json.loads(manifest_summary_path.read_text(encoding="utf-8"))
    replay = json.loads(replay_summary_path.read_text(encoding="utf-8"))
    impact = json.loads(impact_path.read_text(encoding="utf-8"))
    cases = list(manifest.get("cases", []) or [])
    ready_cases = [case for case in cases if case.get("ready_for_rmp_replay")]
    ready_20_cases = [
        case for case in ready_cases if _as_int(case.get("task_count")) == 20
    ]
    ready_20_contexts = {
        str(case.get("context_hash", ""))
        for case in ready_20_cases
        if str(case.get("context_hash", ""))
    }
    nonready_missing_vehicle = [
        case
        for case in cases
        if not case.get("ready_for_rmp_replay")
        and "missing_vehicle_count_for_replay" in list(case.get("issues") or [])
    ]
    metrics = {
        "sources": {
            "report": str(report_path),
            "audit": str(audit_path),
            "manifest": str(manifest_path),
            "manifest_summary": str(manifest_summary_path),
            "replay": str(replay_summary_path),
            "impact": str(impact_path),
        },
        "report_exists": report_path.exists(),
        "files_scanned": _as_int(audit.get("files_scanned")),
        "capture_event_count": _as_int(audit.get("event_count")),
        "captured_journey_count": _as_int(audit.get("captured_journey_count")),
        "manifest_case_count": _as_int(manifest_summary.get("case_count")),
        "manifest_ready_case_count": _as_int(manifest_summary.get("ready_case_count")),
        "manifest_candidate_count": _as_int(manifest_summary.get("candidate_count")),
        "ready_20_case_count": len(ready_20_cases),
        "ready_20_context_count": len(ready_20_contexts),
        "nonready_missing_vehicle_count": len(nonready_missing_vehicle),
        "replay_ready_case_count": _as_int(replay.get("ready_case_count")),
        "replay_all_checks_pass": bool(replay.get("all_checks_pass")),
        "replay_control_rmp_solved": bool(
            (replay.get("checks") or {}).get("control_rmp_solved")
        ),
        "impact_all_checks_pass": bool(impact.get("all_checks_pass")),
        "impact_candidate_row_count": _as_int(impact.get("candidate_row_count")),
        "impact_single_candidate_with_replay_count": _as_int(
            impact.get("single_candidate_with_replay_count")
        ),
        "impact_high_impact_candidate_count": _as_int(
            impact.get("high_impact_candidate_count")
        ),
        "impact_control_unsolved_case_count": _as_int(
            impact.get("control_unsolved_case_count")
        ),
    }
    metrics["check_global_capture_scan_confirms_clean_replay_sample_scarce"] = (
        metrics["report_exists"]
        and bool(audit.get("all_checks_pass"))
        and metrics["files_scanned"] >= 8000
        and metrics["capture_event_count"] == 4
        and metrics["captured_journey_count"] == 9
        and metrics["manifest_case_count"] == 4
        and metrics["manifest_ready_case_count"] == 1
        and metrics["manifest_candidate_count"] == 9
        and metrics["ready_20_case_count"] == 1
        and metrics["ready_20_context_count"] == 1
        and metrics["nonready_missing_vehicle_count"] == 3
        and metrics["replay_ready_case_count"] == 1
        and metrics["replay_all_checks_pass"] is False
        and metrics["replay_control_rmp_solved"] is True
        and metrics["impact_all_checks_pass"] is False
        and metrics["impact_candidate_row_count"] == 9
        and metrics["impact_single_candidate_with_replay_count"] == 4
        and metrics["impact_high_impact_candidate_count"] == 4
        and metrics["impact_control_unsolved_case_count"] == 3
    )
    return metrics


def _counterfactual_replay_candidate_to_capture_gap_metrics(
    candidate_metrics: dict[str, Any],
    global_capture_metrics: dict[str, Any],
    report_path: Path,
) -> dict[str, Any]:
    recommended = list(candidate_metrics.get("recommended_candidate_ids") or [])
    ready_20_context_count = _as_int(
        global_capture_metrics.get("ready_20_context_count")
    )
    candidate_count = _as_int(candidate_metrics.get("candidate_count"))
    low_noise_count = _as_int(
        candidate_metrics.get("low_context_noise_candidate_count")
    )
    metrics = {
        "source": str(report_path),
        "report_exists": report_path.exists(),
        "candidate_count": candidate_count,
        "low_context_noise_candidate_count": low_noise_count,
        "recommended_candidate_ids": recommended,
        "recommended_candidate_count": len(recommended),
        "global_capture_event_count": _as_int(
            global_capture_metrics.get("capture_event_count")
        ),
        "global_ready_20_context_count": ready_20_context_count,
        "global_ready_20_case_count": _as_int(
            global_capture_metrics.get("ready_20_case_count")
        ),
        "global_nonready_missing_vehicle_count": _as_int(
            global_capture_metrics.get("nonready_missing_vehicle_count")
        ),
        "recommended_candidate_minus_ready_20_context_count": (
            len(recommended) - ready_20_context_count
        ),
        "candidate_manifest_ready": bool(
            candidate_metrics.get("check_replay_candidate_manifest_ready")
        ),
        "global_capture_sample_scarce": bool(
            global_capture_metrics.get(
                "check_global_capture_scan_confirms_clean_replay_sample_scarce"
            )
        ),
    }
    metrics["check_replay_candidate_targets_initially_needed_exact_capture"] = (
        metrics["report_exists"]
        and metrics["candidate_manifest_ready"]
        and metrics["global_capture_sample_scarce"]
        and metrics["candidate_count"] == 40
        and metrics["low_context_noise_candidate_count"] == 3
        and metrics["recommended_candidate_count"] == 3
        and metrics["recommended_candidate_ids"]
        == ["replay_candidate_001", "replay_candidate_003", "replay_candidate_004"]
        and metrics["global_capture_event_count"] == 4
        and metrics["global_ready_20_context_count"] == 1
        and metrics["global_nonready_missing_vehicle_count"] == 3
        and metrics["recommended_candidate_minus_ready_20_context_count"] == 2
    )
    return metrics


def _counterfactual_capture_targets_metrics(
    summary_path: Path,
    report_path: Path,
    candidate_gap_metrics: dict[str, Any],
) -> dict[str, Any]:
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    checks = dict(summary.get("checks") or {})
    candidate_ids = list(summary.get("candidate_ids") or [])
    required_fields = list(summary.get("required_payload_fields") or [])
    metrics = {
        "sources": {
            "summary": str(summary_path),
            "report": str(report_path),
        },
        "report_exists": report_path.exists(),
        "target_count": _as_int(summary.get("target_count")),
        "candidate_ids": candidate_ids,
        "exact_context_count": _as_int(summary.get("exact_context_count")),
        "low_context_noise_target_count": _as_int(
            summary.get("low_context_noise_target_count")
        ),
        "mixed_descriptor_context_target_count": _as_int(
            summary.get("mixed_descriptor_context_target_count")
        ),
        "required_payload_field_count": len(required_fields),
        "all_checks_pass": bool(summary.get("all_checks_pass")),
        "checks": checks,
    }
    metrics["check_capture_targets_are_precise_no_certificate_targets"] = (
        metrics["report_exists"]
        and metrics["all_checks_pass"]
        and metrics["target_count"] == 3
        and metrics["candidate_ids"]
        == ["replay_candidate_001", "replay_candidate_003", "replay_candidate_004"]
        and metrics["exact_context_count"] == 3
        and metrics["low_context_noise_target_count"] == 2
        and metrics["mixed_descriptor_context_target_count"] == 1
        and metrics["required_payload_field_count"] >= 15
        and checks.get("all_targets_are_diagnostic_only") is True
        and checks.get("all_targets_require_no_certificate_effect") is True
        and checks.get("all_targets_require_complete_payload") is True
        and checks.get("targets_are_not_replay_ready_without_capture") is True
        and candidate_gap_metrics[
            "check_replay_candidate_targets_initially_needed_exact_capture"
        ]
    )
    return metrics


def _counterfactual_capture_target_coverage_metrics(
    summary_path: Path,
    report_path: Path,
    capture_targets_metrics: dict[str, Any],
) -> dict[str, Any]:
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    checks = dict(summary.get("checks") or {})
    metrics = {
        "sources": {
            "summary": str(summary_path),
            "report": str(report_path),
        },
        "report_exists": report_path.exists(),
        "target_count": _as_int(summary.get("target_count")),
        "capture_event_count": _as_int(summary.get("capture_event_count")),
        "target_with_near_match_count": _as_int(
            summary.get("target_with_near_match_count")
        ),
        "target_with_exact_capture_count": _as_int(
            summary.get("target_with_exact_capture_count")
        ),
        "uncovered_target_count": _as_int(summary.get("uncovered_target_count")),
        "all_checks_pass": bool(summary.get("all_checks_pass")),
        "checks": checks,
    }
    metrics["check_capture_targets_have_partial_exact_capture_coverage"] = (
        metrics["report_exists"]
        and metrics["all_checks_pass"]
        and metrics["target_count"] == capture_targets_metrics["target_count"] == 3
        and metrics["capture_event_count"] == 104
        and metrics["target_with_near_match_count"] == 3
        and metrics["target_with_exact_capture_count"] == 2
        and metrics["uncovered_target_count"] == 1
        and checks.get("has_replay_ready_exact_capture") is True
        and checks.get("near_matches_do_not_count_as_exact_capture") is True
        and checks.get("targets_still_need_new_capture") is True
    )
    return metrics


def _counterfactual_target_tranq20_replay_metrics(
    report_path: Path,
    audit_path: Path,
    manifest_path: Path,
    replay_path: Path,
    impact_path: Path,
) -> dict[str, Any]:
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    replay = json.loads(replay_path.read_text(encoding="utf-8"))
    impact = json.loads(impact_path.read_text(encoding="utf-8"))
    try:
        best_delta = float(impact.get("best_objective_delta"))
    except (TypeError, ValueError):
        best_delta = 0.0
    metrics = {
        "sources": {
            "report": str(report_path),
            "audit": str(audit_path),
            "manifest": str(manifest_path),
            "replay": str(replay_path),
            "impact": str(impact_path),
        },
        "report_exists": report_path.exists(),
        "capture_event_count": _as_int(audit.get("event_count")),
        "captured_journey_count": _as_int(audit.get("captured_journey_count")),
        "returned_journey_count": _as_int(audit.get("returned_journey_count")),
        "capture_all_checks_pass": bool(audit.get("all_checks_pass")),
        "manifest_case_count": _as_int(manifest.get("case_count")),
        "manifest_ready_case_count": _as_int(manifest.get("ready_case_count")),
        "manifest_candidate_count": _as_int(manifest.get("candidate_count")),
        "manifest_treatment_count": _as_int(manifest.get("treatment_count")),
        "manifest_all_checks_pass": bool(manifest.get("all_checks_pass")),
        "replay_case_count": _as_int(replay.get("case_count")),
        "replay_ready_case_count": _as_int(replay.get("ready_case_count")),
        "replay_improving_treatment_count": _as_int(
            replay.get("improving_treatment_count")
        ),
        "replay_changed_treatment_count": _as_int(replay.get("changed_treatment_count")),
        "replay_all_checks_pass": bool(replay.get("all_checks_pass")),
        "impact_candidate_row_count": _as_int(impact.get("candidate_row_count")),
        "impact_high_impact_candidate_count": _as_int(
            impact.get("high_impact_candidate_count")
        ),
        "impact_noop_candidate_count": _as_int(impact.get("noop_candidate_count")),
        "impact_full_batch_count": _as_int(impact.get("full_batch_count")),
        "impact_full_batch_improved_count": _as_int(
            impact.get("full_batch_improved_count")
        ),
        "impact_best_objective_delta": best_delta,
        "impact_all_checks_pass": bool(impact.get("all_checks_pass")),
    }
    metrics["check_tranq20_target_replay_has_local_rmp_impact"] = (
        metrics["report_exists"]
        and metrics["capture_all_checks_pass"]
        and metrics["capture_event_count"] == 4
        and metrics["captured_journey_count"] == 26
        and metrics["manifest_all_checks_pass"]
        and metrics["manifest_ready_case_count"] == 4
        and metrics["manifest_candidate_count"] == 26
        and metrics["manifest_treatment_count"] == 41
        and metrics["replay_all_checks_pass"]
        and metrics["replay_improving_treatment_count"] == 37
        and metrics["impact_all_checks_pass"]
        and metrics["impact_high_impact_candidate_count"] == 26
        and metrics["impact_full_batch_improved_count"] == 4
        and metrics["impact_best_objective_delta"] < -1.0e-9
    )
    return metrics


def _counterfactual_target_001_002_replay_metrics(
    report_path: Path,
    audit_path: Path,
    manifest_path: Path,
    replay_path: Path,
    impact_path: Path,
) -> dict[str, Any]:
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    replay = json.loads(replay_path.read_text(encoding="utf-8"))
    impact = json.loads(impact_path.read_text(encoding="utf-8"))
    try:
        best_delta = float(impact.get("best_objective_delta"))
    except (TypeError, ValueError):
        best_delta = 0.0
    metrics = {
        "sources": {
            "report": str(report_path),
            "audit": str(audit_path),
            "manifest": str(manifest_path),
            "replay": str(replay_path),
            "impact": str(impact_path),
        },
        "report_exists": report_path.exists(),
        "capture_event_count": _as_int(audit.get("event_count")),
        "captured_journey_count": _as_int(audit.get("captured_journey_count")),
        "returned_journey_count": _as_int(audit.get("returned_journey_count")),
        "capture_all_checks_pass": bool(audit.get("all_checks_pass")),
        "manifest_case_count": _as_int(manifest.get("case_count")),
        "manifest_ready_case_count": _as_int(manifest.get("ready_case_count")),
        "manifest_candidate_count": _as_int(manifest.get("candidate_count")),
        "manifest_treatment_count": _as_int(manifest.get("treatment_count")),
        "manifest_all_checks_pass": bool(manifest.get("all_checks_pass")),
        "replay_case_count": _as_int(replay.get("case_count")),
        "replay_ready_case_count": _as_int(replay.get("ready_case_count")),
        "replay_improving_treatment_count": _as_int(
            replay.get("improving_treatment_count")
        ),
        "replay_changed_treatment_count": _as_int(replay.get("changed_treatment_count")),
        "replay_all_checks_pass": bool(replay.get("all_checks_pass")),
        "impact_candidate_row_count": _as_int(impact.get("candidate_row_count")),
        "impact_high_impact_candidate_count": _as_int(
            impact.get("high_impact_candidate_count")
        ),
        "impact_noop_candidate_count": _as_int(impact.get("noop_candidate_count")),
        "impact_full_batch_count": _as_int(impact.get("full_batch_count")),
        "impact_full_batch_improved_count": _as_int(
            impact.get("full_batch_improved_count")
        ),
        "impact_best_objective_delta": best_delta,
        "impact_all_checks_pass": bool(impact.get("all_checks_pass")),
    }
    metrics["check_target_001_002_replay_has_local_rmp_impact"] = (
        metrics["report_exists"]
        and metrics["capture_all_checks_pass"]
        and metrics["capture_event_count"] == 66
        and metrics["captured_journey_count"] == 176
        and metrics["manifest_all_checks_pass"]
        and metrics["manifest_ready_case_count"] == 66
        and metrics["manifest_candidate_count"] == 176
        and metrics["manifest_treatment_count"] == 440
        and metrics["replay_all_checks_pass"]
        and metrics["replay_improving_treatment_count"] == 288
        and metrics["replay_changed_treatment_count"] == 353
        and metrics["impact_all_checks_pass"]
        and metrics["impact_high_impact_candidate_count"] == 117
        and metrics["impact_noop_candidate_count"] == 59
        and metrics["impact_full_batch_improved_count"] == 57
        and metrics["impact_best_objective_delta"] < -1.0e-9
    )
    return metrics


def _target002_reproduction_gap_metrics(
    report_path: Path,
    mirror_summary_path: Path,
) -> dict[str, Any]:
    text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    rows = _read_csv(mirror_summary_path) if mirror_summary_path.exists() else []
    row = rows[0] if rows else {}
    active_before = str(row.get("early_column_active_hash_before_sequence") or "")
    active_after = str(row.get("early_column_active_hash_after_sequence") or "")
    primary_task_sets = str(row.get("early_column_primary_task_set_sequence") or "")
    metrics = {
        "sources": {
            "report": str(report_path),
            "mirror_summary": str(mirror_summary_path),
        },
        "report_exists": report_path.exists(),
        "mirror_summary_exists": mirror_summary_path.exists(),
        "mirror_row_count": len(rows),
        "mirror_active_hash_before_sequence": active_before,
        "mirror_active_hash_after_sequence": active_after,
        "mirror_primary_task_set_sequence": primary_task_sets,
        "report_mentions_old_phase10h_path": "427b1308ea279e0c" in text,
        "report_mentions_target_context": "16862add48072518" in text,
        "report_mentions_current_drift_path": "6907bf1e60739a97" in text
        and "a37fc1e4e8451f9b" in text,
        "report_mentions_no_capture_mirror": (
            "root_cause_target002_current_code_no_capture_mirror_20260613" in text
        ),
    }
    metrics["check_target002_gap_is_cg1_trajectory_drift"] = (
        metrics["report_exists"]
        and metrics["mirror_summary_exists"]
        and metrics["mirror_row_count"] == 1
        and "c6ea96127d7c5d7b" in active_before
        and "6907bf1e60739a97" in active_before
        and "a37fc1e4e8451f9b" in active_before
        and "6907bf1e60739a97" in active_after
        and "a37fc1e4e8451f9b" in active_after
        and "[[4,5,8],[4,12,14],[2,20]]" in primary_task_sets
        and metrics["report_mentions_old_phase10h_path"]
        and metrics["report_mentions_target_context"]
        and metrics["report_mentions_current_drift_path"]
        and metrics["report_mentions_no_capture_mirror"]
    )
    return metrics


def _target002_pt03_recovery_metrics(
    report_path: Path,
    mirror_summary_path: Path,
    target_coverage_summary_path: Path,
    audit_summary_path: Path,
    manifest_summary_path: Path,
    replay_summary_path: Path,
    impact_summary_path: Path,
) -> dict[str, Any]:
    text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    mirror_rows = _read_csv(mirror_summary_path) if mirror_summary_path.exists() else []
    coverage = (
        json.loads(target_coverage_summary_path.read_text(encoding="utf-8"))
        if target_coverage_summary_path.exists()
        else {}
    )
    audit = (
        json.loads(audit_summary_path.read_text(encoding="utf-8"))
        if audit_summary_path.exists()
        else {}
    )
    manifest = (
        json.loads(manifest_summary_path.read_text(encoding="utf-8"))
        if manifest_summary_path.exists()
        else {}
    )
    replay = (
        json.loads(replay_summary_path.read_text(encoding="utf-8"))
        if replay_summary_path.exists()
        else {}
    )
    impact = (
        json.loads(impact_summary_path.read_text(encoding="utf-8"))
        if impact_summary_path.exists()
        else {}
    )
    target_results = list(coverage.get("target_results", []) or [])
    target002 = next(
        (
            target
            for target in target_results
            if target.get("target_id") == "capture_target_002"
        ),
        {},
    )
    active_before_sequences = [
        str(row.get("early_column_active_hash_before_sequence") or "")
        for row in mirror_rows
    ]
    primary_task_set_sequences = [
        str(row.get("early_column_primary_task_set_sequence") or "")
        for row in mirror_rows
    ]
    metrics = {
        "sources": {
            "report": str(report_path),
            "mirror_summary": str(mirror_summary_path),
            "target_coverage_summary": str(target_coverage_summary_path),
            "audit_summary": str(audit_summary_path),
            "manifest_summary": str(manifest_summary_path),
            "replay_summary": str(replay_summary_path),
            "impact_summary": str(impact_summary_path),
        },
        "report_exists": report_path.exists(),
        "mirror_summary_exists": mirror_summary_path.exists(),
        "mirror_row_count": len(mirror_rows),
        "mirror_all_recover_target_context": bool(
            mirror_rows
            and all("16862add48072518" in sequence for sequence in active_before_sequences)
        ),
        "mirror_all_recover_phase10h_path": bool(
            mirror_rows
            and all(
                "427b1308ea279e0c" in sequence
                and "16862add48072518" in sequence
                for sequence in active_before_sequences
            )
        ),
        "mirror_primary_task_set_sequences": primary_task_set_sequences,
        "coverage_all_checks_pass": bool(coverage.get("all_checks_pass")),
        "coverage_target_count": _as_int(coverage.get("target_count")),
        "coverage_capture_event_count": _as_int(coverage.get("capture_event_count")),
        "coverage_target_with_exact_capture_count": _as_int(
            coverage.get("target_with_exact_capture_count")
        ),
        "coverage_uncovered_target_count": _as_int(
            coverage.get("uncovered_target_count")
        ),
        "target002_exact_target_match_count": _as_int(
            target002.get("exact_target_match_count")
        ),
        "target002_covered_by_replay_ready_exact_capture": bool(
            target002.get("covered_by_replay_ready_exact_capture")
        ),
        "audit_all_checks_pass": bool(audit.get("all_checks_pass")),
        "manifest_all_checks_pass": bool(manifest.get("all_checks_pass")),
        "manifest_case_count": _as_int(manifest.get("case_count")),
        "manifest_ready_case_count": _as_int(manifest.get("ready_case_count")),
        "manifest_candidate_count": _as_int(manifest.get("candidate_count")),
        "replay_all_checks_pass": bool(replay.get("all_checks_pass")),
        "replay_case_count": _as_int(replay.get("case_count")),
        "impact_all_checks_pass": bool(impact.get("all_checks_pass")),
        "impact_case_count": _as_int(impact.get("case_count")),
        "impact_candidate_row_count": _as_int(impact.get("candidate_row_count")),
        "impact_high_impact_candidate_count": _as_int(
            impact.get("high_impact_candidate_count")
        ),
        "impact_noop_candidate_count": _as_int(impact.get("noop_candidate_count")),
        "impact_full_batch_count": _as_int(impact.get("full_batch_count")),
        "impact_full_batch_improved_count": _as_int(
            impact.get("full_batch_improved_count")
        ),
        "impact_best_objective_delta": impact.get("best_objective_delta"),
        "report_mentions_pt02_drift": "pricing_time_limit=0.2" in text
        and "6907bf1e60739a97" in text
        and "a37fc1e4e8451f9b" in text,
        "report_mentions_pt03_recovery": "pricing_time_limit=0.3" in text
        and "16862add48072518" in text,
        "report_mentions_selector_shift": (
            "has_replay_calibrated_selector_candidate = true" in text
            and "has_production_validated_selector = false" in text
        ),
    }
    try:
        best_delta = float(metrics["impact_best_objective_delta"])
    except (TypeError, ValueError):
        best_delta = 0.0
    metrics["check_target002_pt03_recovery_and_exact_replay"] = (
        metrics["report_exists"]
        and metrics["mirror_summary_exists"]
        and metrics["mirror_row_count"] == 3
        and metrics["mirror_all_recover_target_context"]
        and metrics["mirror_all_recover_phase10h_path"]
        and metrics["coverage_all_checks_pass"]
        and metrics["coverage_target_count"] == 3
        and metrics["coverage_capture_event_count"] == 114
        and metrics["coverage_target_with_exact_capture_count"] == 3
        and metrics["coverage_uncovered_target_count"] == 0
        and metrics["target002_exact_target_match_count"] >= 2
        and metrics["target002_covered_by_replay_ready_exact_capture"]
        and metrics["audit_all_checks_pass"]
        and metrics["manifest_all_checks_pass"]
        and metrics["manifest_case_count"] == 10
        and metrics["manifest_ready_case_count"] == 10
        and metrics["manifest_candidate_count"] == 73
        and metrics["replay_all_checks_pass"]
        and metrics["replay_case_count"] == 10
        and metrics["impact_all_checks_pass"]
        and metrics["impact_case_count"] == 10
        and metrics["impact_candidate_row_count"] == 73
        and metrics["impact_high_impact_candidate_count"] == 62
        and metrics["impact_noop_candidate_count"] == 11
        and metrics["impact_full_batch_count"] == 10
        and metrics["impact_full_batch_improved_count"] == 8
        and best_delta < -1.0e-9
        and metrics["report_mentions_pt02_drift"]
        and metrics["report_mentions_pt03_recovery"]
        and metrics["report_mentions_selector_shift"]
    )
    return metrics


def _counterfactual_replay_selector_gate_metrics(path: Path) -> dict[str, Any]:
    summary = json.loads(path.read_text(encoding="utf-8"))
    full_true_rc = (
        summary.get("full_sample_best_by_feature", {})
        .get("true_reduced_cost", {})
        .get("metrics", {})
    )
    context_true_rc = (
        summary.get("holdout_by_feature", {})
        .get("context_hash", {})
        .get("true_reduced_cost", {})
        .get("micro", {})
    )
    instance_true_rc = (
        summary.get("holdout_by_feature", {})
        .get("instance", {})
        .get("true_reduced_cost", {})
        .get("micro", {})
    )
    dataset_true_rc = (
        summary.get("holdout_by_feature", {})
        .get("impact_dataset", {})
        .get("true_reduced_cost", {})
        .get("micro", {})
    )
    dataset_train_best = (
        summary.get("holdout_train_best", {})
        .get("impact_dataset", {})
        .get("micro", {})
    )
    passing_features = list(summary.get("passing_features_all_holdouts", []) or [])
    checks = dict(summary.get("checks", {}))
    label_counts = dict(summary.get("label_counts", {}))
    metrics = {
        "source": str(path),
        "all_checks_pass": bool(summary.get("all_checks_pass")),
        "row_count": _as_int(summary.get("row_count")),
        "label_counts": label_counts,
        "context_count": _as_int(summary.get("context_count")),
        "instance_count": _as_int(summary.get("instance_count")),
        "impact_dataset_count": _as_int(summary.get("impact_dataset_count")),
        "strict_gate": dict(summary.get("strict_gate", {})),
        "full_sample_true_rc": {
            key: full_true_rc.get(key)
            for key in ("precision", "recall", "tp", "fp", "tn", "fn", "total")
        },
        "context_holdout_true_rc": {
            key: context_true_rc.get(key)
            for key in ("precision", "recall", "tp", "fp", "tn", "fn", "total")
        },
        "instance_holdout_true_rc": {
            key: instance_true_rc.get(key)
            for key in ("precision", "recall", "tp", "fp", "tn", "fn", "total")
        },
        "dataset_holdout_true_rc": {
            key: dataset_true_rc.get(key)
            for key in ("precision", "recall", "tp", "fp", "tn", "fn", "total")
        },
        "dataset_holdout_train_best": {
            key: dataset_train_best.get(key)
            for key in ("precision", "recall", "tp", "fp", "tn", "fn", "total")
        },
        "passing_features_all_holdouts": passing_features,
        "passing_feature_count": len(passing_features),
        "checks": checks,
    }
    metrics["check_exact_replay_selector_gate_rejects_simple_rules"] = (
        metrics["all_checks_pass"]
        and metrics["row_count"] == 207
        and label_counts.get("improved") == 147
        and label_counts.get("noop") == 60
        and metrics["context_count"] == 22
        and metrics["instance_count"] == 4
        and metrics["impact_dataset_count"] == 4
        and (full_true_rc.get("precision") or 0.0) >= 0.85
        and (full_true_rc.get("recall") or 0.0) >= 0.85
        and _as_int(context_true_rc.get("fp")) > 0
        and _as_int(context_true_rc.get("fn")) > 0
        and (instance_true_rc.get("recall") or 0.0) < 0.5
        and (dataset_true_rc.get("precision") or 0.0) < 0.75
        and (dataset_train_best.get("precision") or 0.0) < 0.75
        and not passing_features
        and checks.get("has_exact_replay_rows") is True
        and checks.get("full_sample_true_rc_rule_looks_promising") is True
        and checks.get("dataset_holdout_true_rc_rule_fails") is True
        and checks.get("no_single_feature_passes_all_holdout_gates") is True
        and checks.get("train_best_dataset_holdout_fails") is True
        and checks.get("post_treatment_features_excluded") is True
    )
    return metrics


def _counterfactual_replay_pair_selector_gate_metrics(path: Path) -> dict[str, Any]:
    summary = json.loads(path.read_text(encoding="utf-8"))
    full_pair = dict(summary.get("full_sample_best_pair", {}) or {})
    full_metrics = dict(full_pair.get("metrics", {}) or {})
    holdouts = dict(summary.get("holdout_train_best_pair", {}) or {})
    context_micro = dict((holdouts.get("context_hash", {}) or {}).get("micro", {}) or {})
    instance_micro = dict((holdouts.get("instance", {}) or {}).get("micro", {}) or {})
    dataset_micro = dict((holdouts.get("impact_dataset", {}) or {}).get("micro", {}) or {})
    checks = dict(summary.get("checks", {}) or {})
    label_counts = dict(summary.get("label_counts", {}) or {})
    metrics = {
        "source": str(path),
        "all_checks_pass": bool(summary.get("all_checks_pass")),
        "row_count": _as_int(summary.get("row_count")),
        "label_counts": label_counts,
        "context_count": _as_int(summary.get("context_count")),
        "instance_count": _as_int(summary.get("instance_count")),
        "impact_dataset_count": _as_int(summary.get("impact_dataset_count")),
        "full_sample_best_pair": {
            "rule": full_pair.get("rule"),
            "metrics": {
                key: full_metrics.get(key)
                for key in ("precision", "recall", "tp", "fp", "tn", "fn", "total")
            },
        },
        "context_holdout_pair": {
            key: context_micro.get(key)
            for key in ("precision", "recall", "tp", "fp", "tn", "fn", "total")
        },
        "instance_holdout_pair": {
            key: instance_micro.get(key)
            for key in ("precision", "recall", "tp", "fp", "tn", "fn", "total")
        },
        "dataset_holdout_pair": {
            key: dataset_micro.get(key)
            for key in ("precision", "recall", "tp", "fp", "tn", "fn", "total")
        },
        "context_pair_passes_strict_gate": bool(
            (holdouts.get("context_hash", {}) or {}).get("passes_strict_gate")
        ),
        "instance_pair_passes_strict_gate": bool(
            (holdouts.get("instance", {}) or {}).get("passes_strict_gate")
        ),
        "dataset_pair_passes_strict_gate": bool(
            (holdouts.get("impact_dataset", {}) or {}).get("passes_strict_gate")
        ),
        "checks": checks,
    }
    metrics["passing_holdout_gate_count"] = sum(
        1
        for key in (
            "context_pair_passes_strict_gate",
            "instance_pair_passes_strict_gate",
            "dataset_pair_passes_strict_gate",
        )
        if metrics[key]
    )
    metrics["check_exact_replay_pair_selector_gate_rejects_simple_pairs"] = (
        metrics["all_checks_pass"]
        and metrics["row_count"] == 207
        and label_counts.get("improved") == 147
        and label_counts.get("noop") == 60
        and metrics["context_count"] == 22
        and metrics["instance_count"] == 4
        and metrics["impact_dataset_count"] == 4
        and (full_metrics.get("precision") or 0.0) >= 0.95
        and (full_metrics.get("recall") or 0.0) >= 0.5
        and (context_micro.get("recall") or 0.0) < 0.5
        and (instance_micro.get("precision") or 0.0) < 0.75
        and (dataset_micro.get("precision") or 0.0) < 0.75
        and metrics["passing_holdout_gate_count"] == 0
        and checks.get("full_sample_pair_rule_looks_promising") is True
        and checks.get("context_holdout_pair_rule_fails", True) is True
        and checks.get("instance_holdout_pair_rule_fails") is True
        and checks.get("dataset_holdout_pair_rule_fails") is True
        and checks.get("no_pair_rule_passes_all_holdout_gates") is True
        and checks.get("post_treatment_features_excluded") is True
    )
    return metrics


def _compact_model_metrics(payload: dict[str, Any]) -> dict[str, Any]:
    models = dict(payload.get("models", {}) or {})
    return {
        model_name: {
            key: model.get(key)
            for key in ("precision", "recall", "tp", "fp", "tn", "fn", "total")
        }
        for model_name, model in models.items()
    }


def _counterfactual_replay_model_selector_gate_metrics(path: Path) -> dict[str, Any]:
    summary = json.loads(path.read_text(encoding="utf-8"))
    checks = dict(summary.get("checks", {}) or {})
    label_counts = dict(summary.get("label_counts", {}) or {})
    context_gate = dict(
        (summary.get("leave_one_context", {}) or {}).get("strict_selector_gate", {})
    )
    instance_gate = dict(
        (summary.get("leave_one_instance", {}) or {}).get("strict_selector_gate", {})
    )
    dataset_gate = dict(
        (summary.get("leave_one_dataset", {}) or {}).get("strict_selector_gate", {})
    )
    context_passing = list(context_gate.get("passing_models", []) or [])
    instance_passing = list(instance_gate.get("passing_models", []) or [])
    dataset_passing = list(dataset_gate.get("passing_models", []) or [])
    all_holdout_passing = sorted(
        set(context_passing).intersection(instance_passing).intersection(dataset_passing)
    )
    metrics = {
        "source": str(path),
        "all_checks_pass": bool(summary.get("all_checks_pass")),
        "row_count": _as_int(summary.get("row_count")),
        "label_counts": label_counts,
        "context_count": _as_int(summary.get("context_count")),
        "instance_count": _as_int(summary.get("instance_count")),
        "impact_dataset_count": _as_int(summary.get("impact_dataset_count")),
        "context_passing_models": context_passing,
        "instance_passing_models": instance_passing,
        "dataset_passing_models": dataset_passing,
        "all_holdout_passing_models": all_holdout_passing,
        "context_models": _compact_model_metrics(
            dict(summary.get("leave_one_context", {}) or {})
        ),
        "instance_models": _compact_model_metrics(
            dict(summary.get("leave_one_instance", {}) or {})
        ),
        "dataset_models": _compact_model_metrics(
            dict(summary.get("leave_one_dataset", {}) or {})
        ),
        "checks": checks,
    }
    metrics["check_exact_replay_model_selector_gate_rejects_simple_models"] = (
        metrics["all_checks_pass"]
        and metrics["row_count"] == 207
        and label_counts.get("improved") == 147
        and label_counts.get("noop") == 60
        and metrics["context_count"] == 22
        and metrics["instance_count"] == 4
        and metrics["impact_dataset_count"] == 4
        and bool(context_passing)
        and bool(instance_passing)
        and not dataset_passing
        and not all_holdout_passing
        and checks.get("context_models_have_passing_candidates") is True
        and checks.get("instance_models_have_passing_candidates") is True
        and checks.get("dataset_models_fail_strict_gate") is True
        and checks.get("no_model_passes_all_holdout_gates") is True
        and checks.get("post_treatment_features_excluded") is True
    )
    return metrics


def _selector_gate_with_target002_pt03_metrics(
    selector_path: Path,
    pair_path: Path,
    model_path: Path,
) -> dict[str, Any]:
    selector = _counterfactual_replay_selector_gate_metrics(selector_path)
    pair = _counterfactual_replay_pair_selector_gate_metrics(pair_path)
    model = _counterfactual_replay_model_selector_gate_metrics(model_path)
    expected_features = {
        "true_reduced_cost",
        "cost",
        "new_task_set",
        "strict_replacement_by_cost",
    }
    passing_features = set(selector["passing_features_all_holdouts"])
    metrics = {
        "sources": {
            "selector": str(selector_path),
            "pair": str(pair_path),
            "model": str(model_path),
        },
        "selector": selector,
        "pair": pair,
        "model": model,
        "row_count": selector["row_count"],
        "label_counts": selector["label_counts"],
        "passing_features_all_holdouts": selector[
            "passing_features_all_holdouts"
        ],
        "pair_no_pair_rule_passes_all_holdout_gates": bool(
            pair["checks"].get("no_pair_rule_passes_all_holdout_gates")
        ),
        "model_all_holdout_passing_models": model[
            "all_holdout_passing_models"
        ],
        "post_treatment_excluded": bool(
            selector["checks"].get("post_treatment_features_excluded")
            and pair["checks"].get("post_treatment_features_excluded")
            and model["checks"].get("post_treatment_features_excluded")
        ),
    }
    metrics["check_selector_gate_shift_has_calibrated_candidates"] = (
        metrics["row_count"] == 280
        and metrics["label_counts"].get("improved") == 209
        and metrics["label_counts"].get("noop") == 71
        and expected_features.issubset(passing_features)
        and selector["checks"].get("has_exact_replay_rows") is True
        and selector["checks"].get("has_improved_and_noop_labels") is True
        and selector["checks"].get("no_single_feature_passes_all_holdout_gates")
        is False
        and metrics["pair_no_pair_rule_passes_all_holdout_gates"] is True
        and len(model["all_holdout_passing_models"]) > 0
        and model["checks"].get("no_model_passes_all_holdout_gates") is False
        and metrics["post_treatment_excluded"]
    )
    return metrics


def _replay_calibrated_selector_candidate_metrics(
    summary_path: Path,
    report_path: Path,
) -> dict[str, Any]:
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    labels = dict(summary.get("label_counts", {}) or {})
    rule = dict(summary.get("recommended_selector_rule", {}) or {})
    full = dict(summary.get("recommended_selector_full_sample", {}) or {})
    case_level = dict(summary.get("recommended_selector_case_level", {}) or {})
    production = dict(summary.get("production_validation", {}) or {})
    checks = dict(summary.get("checks", {}) or {})
    threshold = float(rule.get("threshold", 0.0) or 0.0)
    precision = float(full.get("precision", 0.0) or 0.0)
    recall = float(full.get("recall", 0.0) or 0.0)
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    metrics = {
        "source": str(summary_path),
        "report": str(report_path),
        "report_exists": report_path.exists(),
        "all_checks_pass": bool(summary.get("all_checks_pass")),
        "schema_version": summary.get("schema_version"),
        "row_count": _as_int(summary.get("row_count")),
        "label_counts": labels,
        "passing_features_all_holdouts": list(
            summary.get("passing_features_all_holdouts", []) or []
        ),
        "recommended_selector_candidate": summary.get(
            "recommended_selector_candidate"
        ),
        "recommended_selector_rule": rule,
        "recommended_full_sample": full,
        "recommended_case_level": case_level,
        "recommended_false_positive_count": _as_int(
            summary.get("recommended_selector_false_positive_count")
        ),
        "recommended_false_negative_count": _as_int(
            summary.get("recommended_selector_false_negative_count")
        ),
        "production_validation": production,
        "checks": checks,
        "report_phrase_presence": {
            "true_rc_threshold": "true_reduced_cost <= -12.430587" in report_text,
            "false_positive_count": "false_positive_count = 22" in report_text,
            "false_negative_count": "false_negative_count = 31" in report_text,
            "production_not_validated": "production_validated_selector = false"
            in report_text,
        },
    }
    metrics["check_replay_calibrated_selector_candidate_is_ab_only"] = bool(
        metrics["report_exists"]
        and metrics["all_checks_pass"]
        and metrics["schema_version"] == "replay_calibrated_selector_candidate_v1"
        and metrics["row_count"] == 280
        and labels.get("improved") == 209
        and labels.get("noop") == 71
        and metrics["recommended_selector_candidate"]
        == "true_reduced_cost_<=_-12.430587"
        and rule.get("feature") == "true_reduced_cost"
        and rule.get("operator") == "<="
        and abs(threshold - (-12.430587)) <= 1.0e-9
        and full.get("tp") == 178
        and full.get("fp") == 22
        and full.get("tn") == 49
        and full.get("fn") == 31
        and abs(precision - 0.89) <= 1.0e-12
        and abs(recall - 0.8516746411483254) <= 1.0e-12
        and metrics["recommended_false_positive_count"] == 22
        and metrics["recommended_false_negative_count"] == 31
        and case_level.get("selected_only_noop") == 10
        and case_level.get("missed_positive_case") == 12
        and production.get("production_validated_selector") is False
        and production.get("must_not_treat_as_certificate") is True
        and checks.get("production_validation_still_missing") is True
        and all(metrics["report_phrase_presence"].values())
    )
    return metrics


def _calibrated_selector_profile_rows(path: Path) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    rows = _read_csv(path)
    profile_rows = [
        row
        for row in rows
        if row.get("profile") == "strict_worker_current_probe_calibrated_true_rc_20_only"
    ]
    return rows, profile_rows


def _calibrated_selector_ab_profile_smoke_metrics(
    report_path: Path,
    small_csv: Path,
    mt20_apollo_csv: Path,
    tranq20_csv: Path,
    mt20_tranq_csv: Path,
) -> dict[str, Any]:
    script_text = Path(
        "BPC_future/scripts/run_sharded_pulse_roi_calibration.py"
    ).read_text(encoding="utf-8")
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    small_rows, small_profile = _calibrated_selector_profile_rows(small_csv)
    smoke_paths = {
        "mt20_apollo": mt20_apollo_csv,
        "tranq20": tranq20_csv,
        "mt20_tranq": mt20_tranq_csv,
    }
    twenty_profile_rows: dict[str, list[dict[str, str]]] = {}
    for key, path in smoke_paths.items():
        _rows, profile_rows = _calibrated_selector_profile_rows(path)
        twenty_profile_rows[key] = profile_rows

    def unchanged_count(rows: list[dict[str, str]]) -> int:
        return sum(_as_bool(row.get("official_unchanged_vs_baseline")) for row in rows)

    def changed_count(rows: list[dict[str, str]]) -> int:
        return sum(_as_bool(row.get("official_result_changed_vs_baseline")) for row in rows)

    def objective_mismatch_count(rows: list[dict[str, str]]) -> int:
        return sum(_as_bool(row.get("objective_mismatch_vs_baseline")) for row in rows)

    def worker_event_count(rows: list[dict[str, str]]) -> int:
        return sum(_as_int(row.get("worker_events")) for row in rows)

    def worker_triggered_count(rows: list[dict[str, str]]) -> int:
        return sum(_as_bool(row.get("worker_triggered")) for row in rows)

    all_twenty_profile_rows = [
        row for profile_rows in twenty_profile_rows.values() for row in profile_rows
    ]
    metrics = {
        "report": str(report_path),
        "report_exists": report_path.exists(),
        "sources": {
            "small": str(small_csv),
            "mt20_apollo": str(mt20_apollo_csv),
            "tranq20": str(tranq20_csv),
            "mt20_tranq": str(mt20_tranq_csv),
        },
        "profile_defined": (
            "strict_worker_current_probe_calibrated_true_rc_20_only" in script_text
            and "root_cause_calibrated_selector_ab" in script_text
            and "REPLAY_CALIBRATED_TRUE_RC_THRESHOLD = -12.430587" in script_text
        ),
        "small_rows": len(small_rows),
        "small_profile_rows": len(small_profile),
        "small_profile_instances": [row.get("instance") for row in small_profile],
        "small_profile_worker_events": worker_event_count(small_profile),
        "small_profile_worker_triggered_count": worker_triggered_count(small_profile),
        "small_profile_official_changed_count": changed_count(small_profile),
        "small_profile_objective_mismatch_count": objective_mismatch_count(small_profile),
        "small_profile_unchanged_count": unchanged_count(small_profile),
        "twenty_profile_rows": len(all_twenty_profile_rows),
        "twenty_profile_instances": [
            row.get("instance") for row in all_twenty_profile_rows
        ],
        "twenty_profile_worker_events": worker_event_count(all_twenty_profile_rows),
        "twenty_profile_worker_triggered_count": worker_triggered_count(
            all_twenty_profile_rows
        ),
        "twenty_profile_official_changed_count": changed_count(all_twenty_profile_rows),
        "twenty_profile_objective_mismatch_count": objective_mismatch_count(
            all_twenty_profile_rows
        ),
        "twenty_profile_unchanged_count": unchanged_count(all_twenty_profile_rows),
        "twenty_profile_pricing_states": [
            row.get("official_pricing_state") for row in all_twenty_profile_rows
        ],
        "report_phrase_presence": {
            "calibrated_threshold": "min_true_rc = -12.430587" in report_text,
            "small_no_worker": "profile_worker_events = 0" in report_text,
            "not_roi_proof": "不是 ROI 证据" in report_text
            or "不是生产优化证明" in report_text,
            "production_false": "has_production_validated_selector = false"
            in report_text
            and "has_20_walltime_speedup_evidence = false" in report_text,
        },
    }
    metrics["check_calibrated_selector_profile_smoke_is_wiring_only"] = bool(
        metrics["report_exists"]
        and metrics["profile_defined"]
        and metrics["small_rows"] == 6
        and metrics["small_profile_rows"] == 3
        and metrics["small_profile_instances"] == ["very_small", "apollo5", "tranq5"]
        and metrics["small_profile_worker_events"] == 0
        and metrics["small_profile_worker_triggered_count"] == 0
        and metrics["small_profile_official_changed_count"] == 0
        and metrics["small_profile_objective_mismatch_count"] == 0
        and metrics["small_profile_unchanged_count"] == 3
        and metrics["twenty_profile_rows"] == 3
        and metrics["twenty_profile_worker_events"] == 0
        and metrics["twenty_profile_worker_triggered_count"] == 0
        and metrics["twenty_profile_official_changed_count"] == 0
        and metrics["twenty_profile_objective_mismatch_count"] == 0
        and metrics["twenty_profile_unchanged_count"] == 3
        and set(metrics["twenty_profile_pricing_states"]) == {"FOUND_NEGATIVE"}
        and all(metrics["report_phrase_presence"].values())
    )
    return metrics


def _calibrated_selector_hardtail_worker_smoke_metrics(
    report_path: Path,
    csv_path: Path,
) -> dict[str, Any]:
    script_text = Path(
        "BPC_future/scripts/run_sharded_pulse_roi_calibration.py"
    ).read_text(encoding="utf-8")
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    rows = _read_csv(csv_path) if csv_path.exists() else []
    profile_name = (
        "strict_worker_delayed_current_probe_calibrated_true_rc_20_only_"
        "pre_heuristic_coverage_scan"
    )
    profile_rows = [row for row in rows if row.get("profile") == profile_name]
    baseline_rows = [row for row in rows if row.get("profile") == "baseline"]
    row = profile_rows[0] if profile_rows else {}
    next_rmp_delta = _as_float(row.get("pulse_worker_next_rmp_objective_delta"))
    next_dual_l1 = _as_float(row.get("pulse_worker_next_dual_l1_delta"))
    selected_best_true_rc = _as_float(
        row.get("pulse_worker_impact_filter_selected_best_true_rc")
    )
    metrics = {
        "report": str(report_path),
        "report_exists": report_path.exists(),
        "source": str(csv_path),
        "csv_exists": csv_path.exists(),
        "profile_defined": (
            profile_name in script_text
            and "root_cause_calibrated_selector_hardtail_ab" in script_text
            and "root_cause_calibrated_selector_hardtail" in script_text
            and "REPLAY_CALIBRATED_TRUE_RC_THRESHOLD = -12.430587" in script_text
        ),
        "rows": len(rows),
        "baseline_rows": len(baseline_rows),
        "profile_rows": len(profile_rows),
        "profile_instance": row.get("instance"),
        "profile_scale": _as_int(row.get("scale")),
        "profile_status": row.get("status"),
        "profile_pricing_state": row.get("official_pricing_state"),
        "profile_worker_events": _as_int(row.get("worker_events")),
        "profile_worker_triggered": _as_bool(row.get("worker_triggered")),
        "profile_worker_signal_source": row.get("worker_signal_source"),
        "profile_worker_added_journeys": _as_int(row.get("worker_added_journeys")),
        "profile_worker_added_new_task_set_count": _as_int(
            row.get("worker_added_new_task_set_count")
        ),
        "profile_impact_filter_mode": row.get("pulse_worker_impact_filter_mode"),
        "profile_impact_filter_min_true_rc": row.get(
            "pulse_worker_impact_filter_min_true_rc"
        ),
        "profile_impact_filter_candidate_count": _as_int(
            row.get("pulse_worker_impact_filter_candidate_count")
        ),
        "profile_impact_filter_selected_count": _as_int(
            row.get("pulse_worker_impact_filter_selected_count")
        ),
        "profile_impact_filter_dropped_count": _as_int(
            row.get("pulse_worker_impact_filter_dropped_count")
        ),
        "profile_impact_filter_threshold_dropped_count": _as_int(
            row.get("pulse_worker_impact_filter_rc_threshold_dropped_count")
        ),
        "profile_selected_best_true_rc": selected_best_true_rc,
        "profile_next_rmp_objective_delta": next_rmp_delta,
        "profile_next_dual_l1_delta": next_dual_l1,
        "profile_followup_tail_outcome": row.get("pulse_worker_followup_tail_outcome"),
        "profile_followup_first_negative_task_set": row.get(
            "pulse_worker_followup_first_negative_task_set"
        ),
        "profile_followup_first_negative_relation_to_worker": row.get(
            "pulse_worker_followup_first_negative_relation_to_worker"
        ),
        "profile_vs_ordinary_contrast_class": row.get(
            "pulse_worker_vs_ordinary_contrast_class"
        ),
        "profile_official_dual_bound": row.get("official_dual_bound"),
        "profile_objective_mismatch": _as_bool(
            row.get("objective_mismatch_vs_baseline")
        ),
        "profile_official_changed": _as_bool(
            row.get("official_result_changed_vs_baseline")
        ),
        "report_phrase_presence": {
            "profile_name": profile_name in report_text,
            "threshold": "impact_filter_min_true_rc = -12.430587" in report_text,
            "triggered": "worker_added_journeys = 2" in report_text,
            "residual": "disjoint residual negative" in report_text,
            "production_false": "has_production_validated_selector = false"
            in report_text
            and "has_20_walltime_speedup_evidence = false" in report_text,
            "not_proof": "不能作为生产优化证明" in report_text,
        },
    }
    metrics["check_calibrated_selector_hardtail_smoke_is_nonproduction_signal"] = bool(
        metrics["report_exists"]
        and metrics["csv_exists"]
        and metrics["profile_defined"]
        and metrics["rows"] == 2
        and metrics["baseline_rows"] == 1
        and metrics["profile_rows"] == 1
        and metrics["profile_instance"] == "mt20_greedy_apollo_01"
        and metrics["profile_scale"] == 20
        and metrics["profile_status"] == "TIME_LIMIT"
        and metrics["profile_pricing_state"] == "FOUND_NEGATIVE"
        and metrics["profile_worker_events"] >= 1
        and metrics["profile_worker_triggered"]
        and metrics["profile_worker_signal_source"] == "current_context_probe"
        and metrics["profile_worker_added_journeys"] == 2
        and metrics["profile_worker_added_new_task_set_count"] == 2
        and metrics["profile_impact_filter_mode"] == "prefer_new_or_active_support"
        and metrics["profile_impact_filter_min_true_rc"] == "-12.430587"
        and metrics["profile_impact_filter_candidate_count"] == 3
        and metrics["profile_impact_filter_selected_count"] == 2
        and metrics["profile_impact_filter_dropped_count"] == 1
        and metrics["profile_impact_filter_threshold_dropped_count"] == 1
        and selected_best_true_rc is not None
        and selected_best_true_rc < 0.0
        and next_rmp_delta is not None
        and next_rmp_delta < 0.0
        and next_dual_l1 is not None
        and next_dual_l1 > 0.0
        and metrics["profile_followup_tail_outcome"] == "followup_found_negative"
        and metrics["profile_followup_first_negative_task_set"] == "5,8,15"
        and metrics["profile_followup_first_negative_relation_to_worker"]
        == "disjoint_task_set"
        and metrics["profile_vs_ordinary_contrast_class"]
        == "disjoint_residual_after_worker"
        and metrics["profile_official_dual_bound"] == ""
        and not metrics["profile_objective_mismatch"]
        and metrics["profile_official_changed"]
        and all(metrics["report_phrase_presence"].values())
    )
    return metrics


def _calibrated_selector_hardtail_gate_smoke_metrics(
    report_path: Path,
    csv_path: Path,
) -> dict[str, Any]:
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    rows = _read_csv(csv_path) if csv_path.exists() else []
    profile_name = (
        "strict_worker_delayed_current_probe_calibrated_true_rc_20_only_"
        "pre_heuristic_coverage_scan"
    )
    profile_rows = [row for row in rows if row.get("profile") == profile_name]
    by_scale: dict[int, list[dict[str, str]]] = {}
    for row in profile_rows:
        by_scale.setdefault(_as_int(row.get("scale")), []).append(row)
    small_rows = by_scale.get(5, [])
    ten_rows = by_scale.get(10, [])
    twenty_rows = by_scale.get(20, [])
    apollo20 = next(
        (row for row in twenty_rows if row.get("instance") == "mt20_greedy_apollo_01"),
        {},
    )
    tranq20 = next(
        (row for row in twenty_rows if row.get("instance") == "tranq20_01"),
        {},
    )

    def worker_event_count(local_rows: list[dict[str, str]]) -> int:
        return sum(_as_int(row.get("worker_events")) for row in local_rows)

    def worker_triggered_count(local_rows: list[dict[str, str]]) -> int:
        return sum(_as_bool(row.get("worker_triggered")) for row in local_rows)

    def changed_count(local_rows: list[dict[str, str]]) -> int:
        return sum(_as_bool(row.get("official_result_changed_vs_baseline")) for row in local_rows)

    def objective_mismatch_count(local_rows: list[dict[str, str]]) -> int:
        return sum(_as_bool(row.get("objective_mismatch_vs_baseline")) for row in local_rows)

    metrics = {
        "report": str(report_path),
        "report_exists": report_path.exists(),
        "source": str(csv_path),
        "csv_exists": csv_path.exists(),
        "rows": len(rows),
        "profile_rows": len(profile_rows),
        "profile_instances": [row.get("instance") for row in profile_rows],
        "small_profile_rows": len(small_rows),
        "small_worker_events": worker_event_count(small_rows),
        "small_worker_triggered_count": worker_triggered_count(small_rows),
        "small_official_changed_count": changed_count(small_rows),
        "small_objective_mismatch_count": objective_mismatch_count(small_rows),
        "ten_profile_rows": len(ten_rows),
        "ten_worker_events": worker_event_count(ten_rows),
        "ten_worker_triggered_count": worker_triggered_count(ten_rows),
        "ten_official_changed_count": changed_count(ten_rows),
        "ten_objective_mismatch_count": objective_mismatch_count(ten_rows),
        "twenty_profile_rows": len(twenty_rows),
        "twenty_worker_events": worker_event_count(twenty_rows),
        "twenty_worker_triggered_count": worker_triggered_count(twenty_rows),
        "twenty_official_changed_count": changed_count(twenty_rows),
        "twenty_objective_mismatch_count": objective_mismatch_count(twenty_rows),
        "apollo20_worker_added_journeys": _as_int(
            apollo20.get("worker_added_journeys")
        ),
        "apollo20_worker_added_new_task_set_count": _as_int(
            apollo20.get("worker_added_new_task_set_count")
        ),
        "apollo20_next_rmp_objective_delta": _as_float(
            apollo20.get("pulse_worker_next_rmp_objective_delta")
        ),
        "apollo20_next_dual_l1_delta": _as_float(
            apollo20.get("pulse_worker_next_dual_l1_delta")
        ),
        "apollo20_followup_first_negative_task_set": apollo20.get(
            "pulse_worker_followup_first_negative_task_set"
        ),
        "apollo20_followup_first_negative_relation": apollo20.get(
            "pulse_worker_followup_first_negative_relation_to_worker"
        ),
        "apollo20_vs_ordinary_contrast_class": apollo20.get(
            "pulse_worker_vs_ordinary_contrast_class"
        ),
        "apollo20_threshold": apollo20.get(
            "pulse_worker_impact_filter_min_true_rc"
        ),
        "tranq20_worker_events": _as_int(tranq20.get("worker_events")),
        "tranq20_worker_triggered": _as_bool(tranq20.get("worker_triggered")),
        "report_phrase_presence": {
            "scale_table": "| 5 | 2 | 0 | 0 | 0 | 0 |" in report_text,
            "apollo_signal": "pulse_worker_next_rmp_objective_delta = -38.978656"
            in report_text,
            "residual": "disjoint residual negative `[5,8,15]`" in report_text,
            "not_full_no_regression": "不是全量 no-regression 证明"
            in report_text,
            "production_false": "has_production_validated_selector = false"
            in report_text
            and "has_20_walltime_speedup_evidence = false" in report_text,
        },
    }
    metrics["check_calibrated_selector_hardtail_gate_is_guarded_nonproduction"] = bool(
        metrics["report_exists"]
        and metrics["csv_exists"]
        and metrics["rows"] == 12
        and metrics["profile_rows"] == 6
        and metrics["profile_instances"]
        == [
            "apollo5",
            "tranq5",
            "apollo10",
            "tranq10_09",
            "mt20_greedy_apollo_01",
            "tranq20_01",
        ]
        and metrics["small_profile_rows"] == 2
        and metrics["small_worker_events"] == 0
        and metrics["small_worker_triggered_count"] == 0
        and metrics["small_official_changed_count"] == 0
        and metrics["small_objective_mismatch_count"] == 0
        and metrics["ten_profile_rows"] == 2
        and metrics["ten_worker_events"] == 0
        and metrics["ten_worker_triggered_count"] == 0
        and metrics["ten_official_changed_count"] == 0
        and metrics["ten_objective_mismatch_count"] == 0
        and metrics["twenty_profile_rows"] == 2
        and metrics["twenty_worker_events"] == 1
        and metrics["twenty_worker_triggered_count"] == 1
        and metrics["twenty_official_changed_count"] == 1
        and metrics["twenty_objective_mismatch_count"] == 0
        and metrics["apollo20_worker_added_journeys"] == 2
        and metrics["apollo20_worker_added_new_task_set_count"] == 2
        and metrics["apollo20_next_rmp_objective_delta"] == -38.978656
        and metrics["apollo20_next_dual_l1_delta"] == 43.80801
        and metrics["apollo20_followup_first_negative_task_set"] == "5,8,15"
        and metrics["apollo20_followup_first_negative_relation"]
        == "disjoint_task_set"
        and metrics["apollo20_vs_ordinary_contrast_class"]
        == "disjoint_residual_after_worker"
        and metrics["apollo20_threshold"] == "-12.430587"
        and metrics["tranq20_worker_events"] == 0
        and not metrics["tranq20_worker_triggered"]
        and all(metrics["report_phrase_presence"].values())
    )
    return metrics


def _calibrated_selector_hardtail_repeat_gate_metrics(
    report_path: Path,
    csv_path: Path,
) -> dict[str, Any]:
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    rows = _read_csv(csv_path) if csv_path.exists() else []
    profile_name = (
        "strict_worker_delayed_current_probe_calibrated_true_rc_20_only_"
        "pre_heuristic_coverage_scan"
    )
    profile_rows = [row for row in rows if row.get("profile") == profile_name]
    by_scale: dict[int, list[dict[str, str]]] = {}
    for row in profile_rows:
        by_scale.setdefault(_as_int(row.get("scale")), []).append(row)
    small_rows = by_scale.get(5, [])
    ten_rows = by_scale.get(10, [])
    twenty_rows = by_scale.get(20, [])
    apollo20_rows = [
        row for row in twenty_rows if row.get("instance") == "mt20_greedy_apollo_01"
    ]
    tranq20_rows = [row for row in twenty_rows if row.get("instance") == "tranq20_01"]

    def worker_event_count(local_rows: list[dict[str, str]]) -> int:
        return sum(_as_int(row.get("worker_events")) for row in local_rows)

    def worker_triggered_count(local_rows: list[dict[str, str]]) -> int:
        return sum(_as_bool(row.get("worker_triggered")) for row in local_rows)

    def changed_count(local_rows: list[dict[str, str]]) -> int:
        return sum(_as_bool(row.get("official_result_changed_vs_baseline")) for row in local_rows)

    def objective_mismatch_count(local_rows: list[dict[str, str]]) -> int:
        return sum(_as_bool(row.get("objective_mismatch_vs_baseline")) for row in local_rows)

    apollo_deltas = [
        _as_float(row.get("pulse_worker_next_rmp_objective_delta"))
        for row in apollo20_rows
    ]
    apollo_dual_l1 = [
        _as_float(row.get("pulse_worker_next_dual_l1_delta"))
        for row in apollo20_rows
    ]
    metrics = {
        "report": str(report_path),
        "report_exists": report_path.exists(),
        "source": str(csv_path),
        "csv_exists": csv_path.exists(),
        "rows": len(rows),
        "profile_rows": len(profile_rows),
        "profile_instances": [row.get("instance") for row in profile_rows],
        "small_profile_rows": len(small_rows),
        "small_worker_events": worker_event_count(small_rows),
        "small_worker_triggered_count": worker_triggered_count(small_rows),
        "small_official_changed_count": changed_count(small_rows),
        "small_objective_mismatch_count": objective_mismatch_count(small_rows),
        "ten_profile_rows": len(ten_rows),
        "ten_worker_events": worker_event_count(ten_rows),
        "ten_worker_triggered_count": worker_triggered_count(ten_rows),
        "ten_official_changed_count": changed_count(ten_rows),
        "ten_objective_mismatch_count": objective_mismatch_count(ten_rows),
        "twenty_profile_rows": len(twenty_rows),
        "twenty_worker_events": worker_event_count(twenty_rows),
        "twenty_worker_triggered_count": worker_triggered_count(twenty_rows),
        "twenty_official_changed_count": changed_count(twenty_rows),
        "twenty_objective_mismatch_count": objective_mismatch_count(twenty_rows),
        "apollo20_profile_rows": len(apollo20_rows),
        "apollo20_worker_events": worker_event_count(apollo20_rows),
        "apollo20_worker_triggered_count": worker_triggered_count(apollo20_rows),
        "apollo20_worker_added_journeys": [
            _as_int(row.get("worker_added_journeys")) for row in apollo20_rows
        ],
        "apollo20_worker_added_new_task_set_count": [
            _as_int(row.get("worker_added_new_task_set_count"))
            for row in apollo20_rows
        ],
        "apollo20_next_rmp_objective_deltas": apollo_deltas,
        "apollo20_next_dual_l1_deltas": apollo_dual_l1,
        "apollo20_followup_first_negative_task_sets": [
            row.get("pulse_worker_followup_first_negative_task_set")
            for row in apollo20_rows
        ],
        "apollo20_followup_first_negative_relations": [
            row.get("pulse_worker_followup_first_negative_relation_to_worker")
            for row in apollo20_rows
        ],
        "apollo20_vs_ordinary_contrast_classes": [
            row.get("pulse_worker_vs_ordinary_contrast_class")
            for row in apollo20_rows
        ],
        "tranq20_profile_rows": len(tranq20_rows),
        "tranq20_worker_events": worker_event_count(tranq20_rows),
        "tranq20_worker_triggered_count": worker_triggered_count(tranq20_rows),
        "report_phrase_presence": {
            "repeat_count": "--repeat-count 3" in report_text,
            "scale_table": "| 20 | 6 | 3 | 3 | 3 | 0 |" in report_text,
            "apollo_repeated": "worker_added_journeys = 2 each repeat"
            in report_text,
            "residual_repeated": "5,8,15 each repeat" in report_text,
            "production_false": "has_production_validated_selector = false"
            in report_text
            and "has_20_walltime_speedup_evidence = false" in report_text,
            "not_production": "不是 production selector 证明" in report_text
            or "不是 full benchmark" in report_text,
        },
    }
    metrics["check_calibrated_selector_hardtail_repeat_is_stable_but_not_proven"] = bool(
        metrics["report_exists"]
        and metrics["csv_exists"]
        and metrics["rows"] == 36
        and metrics["profile_rows"] == 18
        and metrics["small_profile_rows"] == 6
        and metrics["small_worker_events"] == 0
        and metrics["small_worker_triggered_count"] == 0
        and metrics["small_official_changed_count"] == 0
        and metrics["small_objective_mismatch_count"] == 0
        and metrics["ten_profile_rows"] == 6
        and metrics["ten_worker_events"] == 0
        and metrics["ten_worker_triggered_count"] == 0
        and metrics["ten_official_changed_count"] == 0
        and metrics["ten_objective_mismatch_count"] == 0
        and metrics["twenty_profile_rows"] == 6
        and metrics["twenty_worker_events"] == 3
        and metrics["twenty_worker_triggered_count"] == 3
        and metrics["twenty_official_changed_count"] == 3
        and metrics["twenty_objective_mismatch_count"] == 0
        and metrics["apollo20_profile_rows"] == 3
        and metrics["apollo20_worker_events"] == 3
        and metrics["apollo20_worker_triggered_count"] == 3
        and metrics["apollo20_worker_added_journeys"] == [2, 2, 2]
        and metrics["apollo20_worker_added_new_task_set_count"] == [2, 2, 2]
        and metrics["apollo20_next_rmp_objective_deltas"]
        == [-38.978656, -38.978656, -38.978656]
        and metrics["apollo20_next_dual_l1_deltas"] == [43.80801, 43.80801, 43.80801]
        and metrics["apollo20_followup_first_negative_task_sets"]
        == ["5,8,15", "5,8,15", "5,8,15"]
        and metrics["apollo20_followup_first_negative_relations"]
        == ["disjoint_task_set", "disjoint_task_set", "disjoint_task_set"]
        and metrics["apollo20_vs_ordinary_contrast_classes"]
        == [
            "disjoint_residual_after_worker",
            "disjoint_residual_after_worker",
            "disjoint_residual_after_worker",
        ]
        and metrics["tranq20_profile_rows"] == 3
        and metrics["tranq20_worker_events"] == 0
        and metrics["tranq20_worker_triggered_count"] == 0
        and all(metrics["report_phrase_presence"].values())
    )
    return metrics


def _calibrated_selector_selected20_repeat_ab_metrics(
    report_path: Path,
    csv_path: Path,
) -> dict[str, Any]:
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    rows = _read_csv(csv_path) if csv_path.exists() else []
    profile_name = (
        "strict_worker_delayed_current_probe_calibrated_true_rc_20_only_"
        "pre_heuristic_coverage_scan"
    )
    profile_rows = [row for row in rows if row.get("profile") == profile_name]
    baseline_rows = [row for row in rows if row.get("profile") == "baseline"]
    apollo_rows = [
        row for row in profile_rows if row.get("instance") == "mt20_greedy_apollo_01"
    ]
    tranq_rows = [row for row in profile_rows if row.get("instance") == "tranq20_01"]
    mt_tranq_rows = [
        row for row in profile_rows if row.get("instance") == "mt20_greedy_tranq_01"
    ]
    baseline_by_key = {
        (row.get("instance"), row.get("repeat_index")): row for row in baseline_rows
    }

    def float_delta(row: dict[str, str], field: str) -> float | None:
        base = baseline_by_key.get((row.get("instance"), row.get("repeat_index")), {})
        left = _as_float(base.get(field))
        right = _as_float(row.get(field))
        if left is None or right is None:
            return None
        return round(right - left, 6)

    wall_deltas = [float_delta(row, "wall_time") for row in profile_rows]
    primal_deltas = [float_delta(row, "official_primal_bound") for row in profile_rows]
    apollo_wall_deltas = [float_delta(row, "wall_time") for row in apollo_rows]
    apollo_primal_deltas = [
        float_delta(row, "official_primal_bound") for row in apollo_rows
    ]
    worker_rows = [
        row for row in profile_rows if _as_int(row.get("worker_events")) > 0
    ]
    no_worker_rows = [
        row for row in profile_rows if _as_int(row.get("worker_events")) == 0
    ]
    metrics = {
        "report": str(report_path),
        "report_exists": report_path.exists(),
        "source": str(csv_path),
        "csv_exists": csv_path.exists(),
        "rows": len(rows),
        "baseline_rows": len(baseline_rows),
        "profile_rows": len(profile_rows),
        "profile_instances": [row.get("instance") for row in profile_rows],
        "all_profile_statuses": [row.get("official_status") for row in profile_rows],
        "all_profile_pricing_states": [
            row.get("official_pricing_state") for row in profile_rows
        ],
        "objective_mismatch_count": sum(
            _as_bool(row.get("objective_mismatch_vs_baseline"))
            for row in profile_rows
        ),
        "official_changed_count": sum(
            _as_bool(row.get("official_result_changed_vs_baseline"))
            for row in profile_rows
        ),
        "worker_rows": len(worker_rows),
        "no_worker_rows": len(no_worker_rows),
        "worker_added_journeys": [
            _as_int(row.get("worker_added_journeys")) for row in profile_rows
        ],
        "wall_deltas": wall_deltas,
        "primal_deltas": primal_deltas,
        "apollo_profile_rows": len(apollo_rows),
        "apollo_worker_events": [_as_int(row.get("worker_events")) for row in apollo_rows],
        "apollo_worker_added_journeys": [
            _as_int(row.get("worker_added_journeys")) for row in apollo_rows
        ],
        "apollo_next_rmp_deltas": [
            _as_float(row.get("pulse_worker_next_rmp_objective_delta"))
            for row in apollo_rows
        ],
        "apollo_next_dual_l1": [
            _as_float(row.get("pulse_worker_next_dual_l1_delta"))
            for row in apollo_rows
        ],
        "apollo_wall_deltas": apollo_wall_deltas,
        "apollo_primal_deltas": apollo_primal_deltas,
        "apollo_followup_first_negative_task_sets": [
            row.get("pulse_worker_followup_first_negative_task_set")
            for row in apollo_rows
        ],
        "apollo_followup_first_negative_relations": [
            row.get("pulse_worker_followup_first_negative_relation_to_worker")
            for row in apollo_rows
        ],
        "tranq_worker_events": sum(_as_int(row.get("worker_events")) for row in tranq_rows),
        "mt_tranq_worker_events": sum(
            _as_int(row.get("worker_events")) for row in mt_tranq_rows
        ),
        "report_phrase_presence": {
            "command": "--max-cg-iterations 8" in report_text,
            "all_time_limit": "all status = TIME_LIMIT" in report_text,
            "mixed_primal": "primal 一次改善、一次恶化" in report_text,
            "residual": "residual disjoint negative `[5,8,15]`" in report_text,
            "production_false": "has_production_validated_selector = false"
            in report_text
            and "has_20_walltime_speedup_evidence = false" in report_text,
        },
    }
    metrics["check_selected20_repeat_ab_rejects_production_speedup"] = bool(
        metrics["report_exists"]
        and metrics["csv_exists"]
        and metrics["rows"] == 12
        and metrics["baseline_rows"] == 6
        and metrics["profile_rows"] == 6
        and metrics["profile_instances"]
        == [
            "mt20_greedy_apollo_01",
            "mt20_greedy_apollo_01",
            "tranq20_01",
            "tranq20_01",
            "mt20_greedy_tranq_01",
            "mt20_greedy_tranq_01",
        ]
        and set(metrics["all_profile_statuses"]) == {"TIME_LIMIT"}
        and metrics["objective_mismatch_count"] == 0
        and metrics["official_changed_count"] == 2
        and metrics["worker_rows"] == 2
        and metrics["no_worker_rows"] == 4
        and metrics["worker_added_journeys"] == [2, 2, 0, 0, 0, 0]
        and metrics["apollo_profile_rows"] == 2
        and metrics["apollo_worker_events"] == [1, 1]
        and metrics["apollo_worker_added_journeys"] == [2, 2]
        and metrics["apollo_next_rmp_deltas"] == [-38.978656, -38.978656]
        and metrics["apollo_next_dual_l1"] == [43.80801, 43.80801]
        and metrics["apollo_wall_deltas"] == [-0.041594, -0.059809]
        and metrics["apollo_primal_deltas"] == [-41.372067, 49.762092]
        and metrics["apollo_followup_first_negative_task_sets"]
        == ["5,8,15", "5,8,15"]
        and metrics["apollo_followup_first_negative_relations"]
        == ["disjoint_task_set", "disjoint_task_set"]
        and metrics["tranq_worker_events"] == 0
        and metrics["mt_tranq_worker_events"] == 0
        and all(metrics["report_phrase_presence"].values())
    )
    return metrics


def _counterfactual_replay_dataset_structure_metrics(
    summary_path: Path,
    report_path: Path,
) -> dict[str, Any]:
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    group_summaries = dict(summary.get("group_summaries", {}) or {})
    dataset = dict(group_summaries.get("impact_dataset", {}) or {})
    instance = dict(group_summaries.get("instance", {}) or {})
    context = dict(group_summaries.get("context_hash", {}) or {})
    checks = dict(summary.get("checks", {}) or {})
    metrics = {
        "source": str(summary_path),
        "report": str(report_path),
        "report_exists": report_path.exists(),
        "all_checks_pass": bool(summary.get("all_checks_pass")),
        "row_count": int(summary.get("row_count", 0)),
        "label_counts": dict(summary.get("label_counts", {}) or {}),
        "dataset_group_count": int(dataset.get("group_count", 0)),
        "dataset_mixed_label_group_count": int(
            dataset.get("mixed_label_group_count", 0)
        ),
        "dataset_pure_improved_group_count": int(
            dataset.get("pure_improved_group_count", 0)
        ),
        "dataset_pure_noop_group_count": int(dataset.get("pure_noop_group_count", 0)),
        "context_group_count": int(context.get("group_count", 0)),
        "context_mixed_label_group_count": int(
            context.get("mixed_label_group_count", 0)
        ),
        "context_single_label_row_share": float(
            context.get("single_label_row_share", 0.0) or 0.0
        ),
        "instance_mixed_label_group_count": int(
            instance.get("mixed_label_group_count", 0)
        ),
        "checks": checks,
    }
    metrics["check_exact_replay_dataset_structure_requires_calibration_only"] = bool(
        metrics["report_exists"]
        and metrics["all_checks_pass"]
        and metrics["row_count"] == 207
        and metrics["label_counts"].get("improved") == 147
        and metrics["label_counts"].get("noop") == 60
        and metrics["dataset_group_count"] == 4
        and metrics["dataset_mixed_label_group_count"] == 1
        and metrics["dataset_pure_improved_group_count"] >= 1
        and metrics["dataset_pure_noop_group_count"] >= 1
        and metrics["context_group_count"] == 22
        and metrics["context_mixed_label_group_count"] == 5
        and metrics["context_single_label_row_share"] > 0.5
        and checks.get("dataset_label_coverage_is_sparse") is True
        and checks.get("single_label_dataset_groups_exist") is True
        and checks.get("selector_calibration_should_remain_non_production") is True
    )
    return metrics


def _counterfactual_capture_priority_metrics(
    summary_path: Path,
    report_path: Path,
) -> dict[str, Any]:
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    top_priorities = list(summary.get("top_priorities", []) or [])
    top = dict(top_priorities[0]) if top_priorities else {}
    checks = dict(summary.get("checks", {}) or {})
    metrics = {
        "source": str(summary_path),
        "report": str(report_path),
        "report_exists": report_path.exists(),
        "all_checks_pass": bool(summary.get("all_checks_pass")),
        "candidate_count": int(summary.get("candidate_count", 0)),
        "recommended_candidate_ids": list(
            summary.get("recommended_candidate_ids", []) or []
        ),
        "covered_recommended_candidate_ids": list(
            summary.get("covered_recommended_candidate_ids", []) or []
        ),
        "uncovered_recommended_candidate_ids": list(
            summary.get("uncovered_recommended_candidate_ids", []) or []
        ),
        "dataset_mixed_label_group_count": int(
            summary.get("dataset_mixed_label_group_count", 0)
        ),
        "context_mixed_label_group_count": int(
            summary.get("context_mixed_label_group_count", 0)
        ),
        "context_single_label_row_share": float(
            summary.get("context_single_label_row_share", 0.0) or 0.0
        ),
        "top_priority_candidate_id": top.get("candidate_id"),
        "top_priority_reason": top.get("priority_reason"),
        "top_priority_context_key": top.get("context_key"),
        "top_priority_candidate_risk": top.get("candidate_risk"),
        "top_priority_score": top.get("capture_priority_score"),
        "checks": checks,
    }
    metrics["check_counterfactual_capture_priority_is_calibration_only"] = bool(
        metrics["report_exists"]
        and metrics["all_checks_pass"]
        and metrics["candidate_count"] == 40
        and metrics["top_priority_candidate_id"] == "replay_candidate_003"
        and metrics["top_priority_reason"] == "recommended_target_uncovered"
        and metrics["top_priority_context_key"]
        == "mt20_greedy_apollo_01|3|heuristic|16862add48072518|780.586496"
        and metrics["uncovered_recommended_candidate_ids"] == ["replay_candidate_003"]
        and checks.get("has_uncovered_recommended_target") is True
        and checks.get("top_priority_is_uncovered_recommended_target") is True
        and checks.get("has_additional_uncovered_candidates") is True
        and checks.get("dataset_structure_still_needs_dual_label_coverage") is True
        and checks.get("priority_is_calibration_only") is True
    )
    return metrics


def _optimization_direction_readiness_metrics(checks: dict[str, Any]) -> dict[str, Any]:
    small = checks["small_scale_overhead"]
    current_small = checks["current_small_summary_scan"]
    phase7o = checks["phase7o_worker_roi"]
    phase8q = checks["phase8q_worker_add_columns"]
    selector_models = checks["candidate_selector_models"]
    batch_selector = checks["batch_level_selector"]
    replay_impact = checks["counterfactual_replay_impact_dataset"]
    replay_expansion = checks["counterfactual_replay_capture_expansion"]
    global_capture_scan = checks["counterfactual_replay_global_capture_scan"]
    candidate_capture_gap = checks["counterfactual_replay_candidate_to_capture_gap"]
    capture_targets = checks["counterfactual_capture_targets"]
    target_coverage = checks["counterfactual_capture_target_coverage"]
    tranq20_target_replay = checks["counterfactual_target_tranq20_replay"]
    target_001_002_replay = checks["counterfactual_target_001_002_replay"]
    target002_gap = checks["counterfactual_target002_reproduction_gap"]
    replay_selector_gate = checks["counterfactual_replay_selector_gate"]
    replay_pair_selector_gate = checks["counterfactual_replay_pair_selector_gate"]
    replay_model_selector_gate = checks["counterfactual_replay_model_selector_gate"]
    target002_pt03_recovery = checks["counterfactual_target002_pt03_recovery"]
    selector_gate_with_target002 = checks[
        "counterfactual_replay_selector_gate_with_target002_pt03"
    ]
    replay_calibrated_selector_candidate = checks[
        "replay_calibrated_selector_candidate"
    ]
    calibrated_selector_ab_profile_smoke = checks[
        "calibrated_selector_ab_profile_smoke"
    ]
    replay_dataset_structure = checks["counterfactual_replay_dataset_structure"]
    capture_priority = checks["counterfactual_capture_priority"]
    selector_holdout_status = checks.get("selector_holdout_status", {})
    selector_context_scalar_holdout = checks.get(
        "selector_context_scalar_holdout", {}
    )
    selector_micro_vs_fold_gate = checks.get("selector_micro_vs_fold_gate", {})
    selector_model_micro_vs_fold_gate = checks.get(
        "selector_model_micro_vs_fold_gate", {}
    )
    selector_rule_family_search = checks.get("selector_rule_family_search", {})
    selector_rule_family_search_20only = checks.get(
        "selector_rule_family_search_20only", {}
    )
    selector_rule_family_train_holdout = checks.get(
        "selector_rule_family_train_holdout", {}
    )
    selector_rule_family_train_holdout_20only = checks.get(
        "selector_rule_family_train_holdout_20only", {}
    )
    selector_context_fold_anatomy = checks.get("selector_context_fold_anatomy", {})
    selector_context_feature_anatomy = checks.get(
        "selector_context_feature_anatomy", {}
    )

    real_capture = replay_impact["real_capture"]
    duplicate_noop = replay_impact["duplicate_noop"]
    combined = replay_impact["combined"]
    selector_passing_models = list(
        selector_models["leave_one_dataset"]["strict_selector_gate"]["passing_models"]
    ) + list(
        selector_models["leave_one_instance"]["strict_selector_gate"]["passing_models"]
    )
    pre_batch_lod = batch_selector["leave_one_dataset"]["pre_batch"]
    pre_batch_loi = batch_selector["leave_one_instance"]["pre_batch"]
    has_small_no_regression_guard = bool(
        small["check_nontriggered_no_official_change"]
        and current_small["nontriggered_official_changed"] == 0
    )
    has_task5_noop_no_regression_guard = bool(
        current_small["check_task5_noop_guard_no_official_change"]
    )
    has_task10_noop_no_regression_guard = bool(
        current_small["check_task10_noop_guard_no_official_change"]
    )
    has_task10_triggered_regression_evidence = bool(
        current_small["check_task10_triggered_is_regression_risk"]
    )
    has_20_negative_columns = bool(
        phase8q["pulse_worker_added_journeys"] > 0
        and phase8q["pulse_worker_added_new_task_set_count"] > 0
    )
    try:
        real_capture_best_delta = float(real_capture.get("best_objective_delta"))
    except (TypeError, ValueError):
        real_capture_best_delta = 0.0
    has_local_rmp_impact = bool(
        real_capture["checks"].get("all_replay_controls_solved") is True
        and real_capture["checks"].get("all_single_candidates_have_finite_delta") is True
        and real_capture["high_impact_candidate_count"] > 0
        and real_capture_best_delta < -1.0e-9
    )
    has_noop_counterexample = bool(
        duplicate_noop["checks"].get("all_replay_controls_solved") is True
        and duplicate_noop["checks"].get("all_single_candidates_have_finite_delta") is True
        and duplicate_noop["noop_candidate_count"] > 0
        and duplicate_noop["best_objective_delta"] == 0.0
    )
    replay_selector_passing_feature_count = replay_selector_gate["passing_feature_count"]
    replay_pair_passing_holdout_gate_count = replay_pair_selector_gate[
        "passing_holdout_gate_count"
    ]
    has_replay_calibrated_selector_candidate = bool(
        target002_pt03_recovery["check_target002_pt03_recovery_and_exact_replay"]
        and selector_gate_with_target002[
            "check_selector_gate_shift_has_calibrated_candidates"
        ]
        and replay_calibrated_selector_candidate[
            "check_replay_calibrated_selector_candidate_is_ab_only"
        ]
    )
    has_robust_all_fold_feature_selector = bool(
        selector_micro_vs_fold_gate.get("robust_all_fold_passing_feature_count", 0)
        > 0
    )
    has_robust_all_fold_model_selector = bool(
        selector_model_micro_vs_fold_gate.get(
            "robust_all_fold_passing_model_count", 0
        )
        > 0
    )
    has_robust_all_fold_rule_selector = bool(
        selector_rule_family_search.get(
            "material_all_fold_passing_rule_count", 0
        )
        > 0
        or selector_rule_family_search_20only.get(
            "material_all_fold_passing_rule_count", 0
        )
        > 0
    )
    has_robust_all_fold_selector = bool(
        has_robust_all_fold_feature_selector
        or has_robust_all_fold_model_selector
        or has_robust_all_fold_rule_selector
    )
    # This verifier is intentionally conservative: replay-calibrated gates can
    # propose the next calibration experiment, but only holdout-stable selectors
    # followed by full BPC A/B can validate a production selector.
    has_production_validated_selector = False
    has_full_5_10_production_ab_evidence = False
    has_legacy_selector_rejection_evidence = bool(
        not selector_passing_models
        and replay_selector_passing_feature_count == 0
        and replay_pair_passing_holdout_gate_count == 0
        and not replay_model_selector_gate["all_holdout_passing_models"]
    )
    clean_replay_context_family_count = global_capture_scan["ready_20_context_count"] + (
        1
        if tranq20_target_replay[
            "check_tranq20_target_replay_has_local_rmp_impact"
        ]
        else 0
    ) + (
        1
        if target_001_002_replay[
            "check_target_001_002_replay_has_local_rmp_impact"
        ]
        else 0
    )
    has_multi_context_clean_replay_calibration = bool(
        clean_replay_context_family_count >= 2
    )
    has_20_walltime_speedup_evidence = bool(
        not phase7o["all_time_limit"] or not phase8q["all_time_limit"]
    )
    production_direction_proven = bool(
        has_small_no_regression_guard
        and has_task5_noop_no_regression_guard
        and has_task10_noop_no_regression_guard
        and has_20_negative_columns
        and has_local_rmp_impact
        and has_replay_calibrated_selector_candidate
        and has_robust_all_fold_selector
        and has_production_validated_selector
        and has_full_5_10_production_ab_evidence
        and has_multi_context_clean_replay_calibration
        and has_20_walltime_speedup_evidence
    )
    missing_requirements: list[dict[str, Any]] = []
    if not has_full_5_10_production_ab_evidence:
        missing_requirements.append(
            {
                "requirement": "five_ten_full_no_regression_ab",
                "reason": (
                    "The evidence proves that 5/10 rows are safe when the worker/"
                    "audit/probe path is a no-op, and that triggered 10-task rows "
                    "can worsen wall time and change official results. No full "
                    "production-candidate BPC A/B has yet proved 5/10 no-regression "
                    "while also improving selected 20-task hard repeats."
                ),
                "evidence": {
                    "has_task5_noop_no_regression_guard": (
                        has_task5_noop_no_regression_guard
                    ),
                    "has_task10_noop_no_regression_guard": (
                        has_task10_noop_no_regression_guard
                    ),
                    "has_task10_triggered_regression_evidence": (
                        has_task10_triggered_regression_evidence
                    ),
                    "task10_triggered": current_small["task10_triggered"],
                    "has_production_validated_selector": (
                        has_production_validated_selector
                    ),
                },
                "required_next_evidence": (
                    "Run a production-candidate full BPC A/B that includes the 5-task "
                    "and 10-task regression gates, keeps official results unchanged, "
                    "and simultaneously demonstrates selected 20-task improvement."
                ),
            }
        )
    if not has_production_validated_selector:
        missing_requirements.append(
            {
                "requirement": "production_validated_selector",
                "reason": (
                    "Exact replay now contains calibrated addition-before selector "
                    "candidates, but no selector has passed the required context, "
                    "instance, and dataset holdout gates; therefore no full BPC A/B "
                    "has proven that any candidate preserves 5/10 behavior while "
                    "accelerating selected 20-task hard repeats."
                ),
                "evidence": {
                    "has_replay_calibrated_selector_candidate": (
                        has_replay_calibrated_selector_candidate
                    ),
                    "has_robust_all_fold_feature_selector": (
                        has_robust_all_fold_feature_selector
                    ),
                    "has_robust_all_fold_model_selector": (
                        has_robust_all_fold_model_selector
                    ),
                    "has_robust_all_fold_rule_selector": (
                        has_robust_all_fold_rule_selector
                    ),
                    "has_robust_all_fold_selector": has_robust_all_fold_selector,
                    "selector_holdout_status": selector_holdout_status.get(
                        "status", {}
                    ),
                    "selector_holdout_check_passed": selector_holdout_status.get(
                        "check_selector_holdout_not_production_validated"
                    ),
                    "selector_holdout_task_set_mixed_group_count": (
                        selector_holdout_status.get("task_set_mixed_group_count")
                    ),
                    "selector_holdout_task_sequence_mixed_group_count": (
                        selector_holdout_status.get(
                            "task_sequence_mixed_group_count"
                        )
                    ),
                    "selector_holdout_online_flags_mixed_row_count": (
                        selector_holdout_status.get("online_flags_mixed_row_count")
                    ),
                    "selector_holdout_task_set_true_rc_improved_lower_count": (
                        selector_holdout_status.get(
                            "task_set_true_rc_improved_lower_count"
                        )
                    ),
                    "selector_holdout_task_set_true_rc_noop_lower_count": (
                        selector_holdout_status.get(
                            "task_set_true_rc_noop_lower_count"
                        )
                    ),
                    "context_scalar_control_objective_bin_100_mixed_group_count": (
                        checks.get("selector_context_scalar_candidates", {}).get(
                            "control_objective_bin_100_mixed_group_count"
                        )
                    ),
                    "context_scalar_cheap_scalar_mixed_group_count": (
                        checks.get("selector_context_scalar_candidates", {}).get(
                            "cheap_scalar_mixed_group_count"
                        )
                    ),
                    "context_scalar_holdout_passing_model_count": (
                        selector_context_scalar_holdout.get("passing_model_count")
                    ),
                    "context_scalar_holdout_threshold_context_precision": (
                        selector_context_scalar_holdout.get(
                            "threshold_context_precision"
                        )
                    ),
                    "context_scalar_holdout_threshold_context_recall": (
                        selector_context_scalar_holdout.get(
                            "threshold_context_recall"
                        )
                    ),
                    "context_scalar_holdout_bin100_context_precision": (
                        selector_context_scalar_holdout.get(
                            "bin100_context_precision"
                        )
                    ),
                    "context_scalar_holdout_bin100_context_recall": (
                        selector_context_scalar_holdout.get("bin100_context_recall")
                    ),
                    "micro_vs_fold_robust_all_fold_passing_feature_count": (
                        selector_micro_vs_fold_gate.get(
                            "robust_all_fold_passing_feature_count"
                        )
                    ),
                    "micro_vs_fold_true_rc_context_passing_folds": (
                        f"{selector_micro_vs_fold_gate.get('true_rc_context_passing_fold_count')}/"
                        f"{selector_micro_vs_fold_gate.get('true_rc_context_fold_count')}"
                    ),
                    "micro_vs_fold_new_task_set_dataset_passing_folds": (
                        f"{selector_micro_vs_fold_gate.get('new_task_set_dataset_passing_fold_count')}/"
                        f"{selector_micro_vs_fold_gate.get('new_task_set_dataset_fold_count')}"
                    ),
                    "model_micro_vs_fold_robust_all_fold_passing_model_count": (
                        selector_model_micro_vs_fold_gate.get(
                            "robust_all_fold_passing_model_count"
                        )
                    ),
                    "model_micro_vs_fold_nearest_context_passing_folds": (
                        f"{selector_model_micro_vs_fold_gate.get('nearest_context_passing_fold_count')}/"
                        f"{selector_model_micro_vs_fold_gate.get('nearest_context_fold_count')}"
                    ),
                    "model_micro_vs_fold_shallow_dataset_passing_folds": (
                        f"{selector_model_micro_vs_fold_gate.get('shallow_dataset_passing_fold_count')}/"
                        f"{selector_model_micro_vs_fold_gate.get('shallow_dataset_fold_count')}"
                    ),
                    "rule_family_rule_count": (
                        selector_rule_family_search.get("rule_count")
                    ),
                    "rule_family_strict_all_fold_passing_rule_count": (
                        selector_rule_family_search.get(
                            "strict_all_fold_passing_rule_count"
                        )
                    ),
                    "rule_family_material_all_fold_passing_rule_count": (
                        selector_rule_family_search.get(
                            "material_all_fold_passing_rule_count"
                        )
                    ),
                    "rule_family_best_rule_precision": (
                        selector_rule_family_search.get("best_rule_precision")
                    ),
                    "rule_family_best_rule_recall": (
                        selector_rule_family_search.get("best_rule_recall")
                    ),
                    "rule_family_20only_rule_count": (
                        selector_rule_family_search_20only.get("rule_count")
                    ),
                    "rule_family_20only_material_all_fold_passing_rule_count": (
                        selector_rule_family_search_20only.get(
                            "material_all_fold_passing_rule_count"
                        )
                    ),
                    "rule_family_20only_best_rule_precision": (
                        selector_rule_family_search_20only.get(
                            "best_rule_precision"
                        )
                    ),
                    "rule_family_20only_best_rule_recall": (
                        selector_rule_family_search_20only.get("best_rule_recall")
                    ),
                    "rule_family_train_context_material_passing_folds": (
                        f"{selector_rule_family_train_holdout.get('context_material_passing_fold_count')}/"
                        f"{selector_rule_family_train_holdout.get('context_fold_count')}"
                    ),
                    "rule_family_train_20only_context_material_passing_folds": (
                        f"{selector_rule_family_train_holdout_20only.get('context_material_passing_fold_count')}/"
                        f"{selector_rule_family_train_holdout_20only.get('context_fold_count')}"
                    ),
                    "context_fold_anatomy_twenty_false_positive_no_positive_context_count": (
                        selector_context_fold_anatomy.get(
                            "twenty_false_positive_no_positive_context_count"
                        )
                    ),
                    "context_fold_anatomy_twenty_missed_positive_context_count": (
                        selector_context_fold_anatomy.get(
                            "twenty_missed_positive_context_count"
                        )
                    ),
                    "context_fold_anatomy_twenty_mixed_failure_context_count": (
                        selector_context_fold_anatomy.get(
                            "twenty_mixed_failure_context_count"
                        )
                    ),
                    "context_feature_mixed_instance_group_count": (
                        selector_context_feature_anatomy.get(
                            "mixed_instance_group_count"
                        )
                    ),
                    "context_feature_mixed_dataset_group_count": (
                        selector_context_feature_anatomy.get(
                            "mixed_dataset_group_count"
                        )
                    ),
                    "context_feature_false_positive_no_positive_context_count": (
                        selector_context_feature_anatomy.get(
                            "false_positive_no_positive_context_count"
                        )
                    ),
                    "context_feature_missed_positive_context_count": (
                        selector_context_feature_anatomy.get(
                            "missed_positive_context_count"
                        )
                    ),
                    "calibrated_selector_profile_smoke_ready": (
                        calibrated_selector_ab_profile_smoke[
                            "check_calibrated_selector_profile_smoke_is_wiring_only"
                        ]
                    ),
                    "target002_pt03_exact_recovery": target002_pt03_recovery[
                        "check_target002_pt03_recovery_and_exact_replay"
                    ],
                    "selector_gate_with_target002_passing_features": (
                        selector_gate_with_target002[
                            "passing_features_all_holdouts"
                        ]
                    ),
                    "selector_gate_with_target002_model_all_holdout_passing": (
                        selector_gate_with_target002[
                            "model_all_holdout_passing_models"
                        ]
                    ),
                    "recommended_selector_candidate": (
                        replay_calibrated_selector_candidate[
                            "recommended_selector_candidate"
                        ]
                    ),
                    "recommended_selector_rule": (
                        replay_calibrated_selector_candidate[
                            "recommended_selector_rule"
                        ]
                    ),
                    "recommended_full_sample": (
                        replay_calibrated_selector_candidate[
                            "recommended_full_sample"
                        ]
                    ),
                    "recommended_false_positive_count": (
                        replay_calibrated_selector_candidate[
                            "recommended_false_positive_count"
                        ]
                    ),
                    "recommended_false_negative_count": (
                        replay_calibrated_selector_candidate[
                            "recommended_false_negative_count"
                        ]
                    ),
                    "calibrated_selector_smoke_twenty_worker_triggered_count": (
                        calibrated_selector_ab_profile_smoke[
                            "twenty_profile_worker_triggered_count"
                        ]
                    ),
                    "calibrated_selector_smoke_twenty_pricing_states": (
                        calibrated_selector_ab_profile_smoke[
                            "twenty_profile_pricing_states"
                        ]
                    ),
                    "candidate_selector_passing_models": selector_passing_models,
                    "exact_replay_single_passing_feature_count": (
                        replay_selector_passing_feature_count
                    ),
                    "exact_replay_pair_passing_holdout_gate_count": (
                        replay_pair_passing_holdout_gate_count
                    ),
                    "exact_replay_model_all_holdout_passing_models": (
                        replay_model_selector_gate["all_holdout_passing_models"]
                    ),
                },
                "required_next_evidence": (
                    "First, a selector using only addition-before features must pass "
                    "context, instance, and dataset holdouts on no-certificate-effect "
                    "exact-context replay data. Only then should it enter full BPC "
                    "A/B: 5/10 no-regression plus selected 20-task hard-repeat "
                    "wall-time/gap/status/tail improvement."
                ),
            }
        )
    if not has_20_walltime_speedup_evidence:
        missing_requirements.append(
            {
                "requirement": "twenty_walltime_speedup",
                "reason": (
                    "Existing hard-tail worker and add-column smokes did not "
                    "produce stable 20-task wall-time/status improvement."
                ),
                "evidence": {
                    "phase7o_all_time_limit": phase7o["all_time_limit"],
                    "phase8q_all_time_limit": phase8q["all_time_limit"],
                    "phase7o_rows": phase7o["rows"],
                    "phase8q_rows": phase8q["rows"],
                    "phase7o_worker_events": phase7o["worker_events"],
                    "phase8q_worker_events": phase8q["worker_events"],
                },
                "required_next_evidence": (
                    "A selected 20-task hard repeat A/B must show wall-time, "
                    "gap, status, or final-judge tail improvement while keeping "
                    "official exactness unchanged."
                ),
            }
        )
    next_evidence_gates = {
        "calibration_only_until_selector_passes": True,
        "replay_calibrated_selector_candidate_available": (
            has_replay_calibrated_selector_candidate
        ),
        "robust_all_fold_selector_available": has_robust_all_fold_selector,
        "production_validated_selector_available": has_production_validated_selector,
        "required_selector_holdouts": ("context", "instance", "dataset"),
        "selector_feature_scope": "addition_before_only",
        "require_5_10_no_regression_gate_before_production": True,
        "require_selected_20_hard_repeat_ab_before_production": True,
        "forbidden_shortcuts": (
            "post_addition_or_hindsight_features",
            "single_context_replay_success",
            "worker_negative_columns_without_walltime_roi",
            "certificate_effect",
        ),
    }
    next_evidence_protocol = (
        {
            "gate": "exact_context_capture_and_replay_dataset",
            "purpose": (
                "Grow the calibration set with no-certificate-effect treatment "
                "payloads before proposing a production selector."
            ),
            "required_artifacts": (
                "returned batch payloads",
                "RMP pool snapshot",
                "true dual snapshot",
                "cut snapshot",
                "context hash",
                "candidate/treatment impact rows",
            ),
            "pass_condition": (
                "Multiple 20-task context families contain both high-impact and "
                "noop/replacement examples with solved replay controls."
            ),
            "forbidden_shortcuts": (
                "observational candidate rows without treatment replay",
                "single-context improvement",
                "post-addition labels as online features",
            ),
        },
        {
            "gate": "addition_before_selector",
            "purpose": (
                "Prove that a selector can identify high-impact returned batches "
                "before adding them to the pool."
            ),
            "required_artifacts": (
                "selector definition",
                "feature list",
                "context holdout metrics",
                "instance holdout metrics",
                "dataset holdout metrics",
            ),
            "pass_condition": (
                "Selector uses only addition-before features and passes context, "
                "instance, and dataset gates simultaneously."
            ),
            "forbidden_shortcuts": (
                "true-RC-only threshold from full sample",
                "pair rule that fails any holdout",
                "model that passes context/instance but fails dataset",
                "hindsight active/incumbent features",
            ),
        },
        {
            "gate": "production_candidate_ab",
            "purpose": (
                "Show that the selector is not only locally predictive but improves "
                "the actual exact solve path."
            ),
            "required_artifacts": (
                "5/10 no-regression matrix",
                "selected 20-task hard repeat A/B",
                "official exactness comparison",
                "wall-time/gap/status/tail metrics",
            ),
            "pass_condition": (
                "5/10 official results do not regress and selected 20-task hard "
                "runs show stable wall-time, gap, status, or final-judge tail "
                "improvement."
            ),
            "forbidden_shortcuts": (
                "worker added negative columns without downstream ROI",
                "diagnostic certificate effect",
                "single repeat speedup",
                "5/10 skipped from validation",
            ),
        },
    )
    has_replay_dataset_for_selector_attempt = bool(
        has_multi_context_clean_replay_calibration
        and target_001_002_replay["manifest_ready_case_count"] > 0
        and target_001_002_replay["impact_high_impact_candidate_count"] > 0
        and target_001_002_replay["impact_noop_candidate_count"] > 0
    )
    current_capture_targets_all_covered = bool(
        target002_pt03_recovery["check_target002_pt03_recovery_and_exact_replay"]
        and target002_pt03_recovery["coverage_target_with_exact_capture_count"]
        == capture_targets["target_count"]
        and target002_pt03_recovery["coverage_uncovered_target_count"] == 0
    )
    current_uncovered_recommended_capture_candidate_ids: list[str] = (
        []
        if current_capture_targets_all_covered
        else list(capture_priority["uncovered_recommended_candidate_ids"])
    )
    current_next_capture_priority_candidate_id = (
        None
        if current_capture_targets_all_covered
        else capture_priority["top_priority_candidate_id"]
    )
    next_evidence_protocol_readiness = (
        {
            "gate": "exact_context_capture_and_replay_dataset",
            "current_status": (
                "ready_for_selector_calibration_attempt"
                if has_replay_dataset_for_selector_attempt
                else "not_ready"
            ),
            "passed_for_current_stage": has_replay_dataset_for_selector_attempt,
            "evidence": {
                "clean_replay_context_family_count": clean_replay_context_family_count,
                "dataset_mixed_label_group_count": replay_dataset_structure[
                    "dataset_mixed_label_group_count"
                ],
                "context_mixed_label_group_count": replay_dataset_structure[
                    "context_mixed_label_group_count"
                ],
                "context_single_label_row_share": replay_dataset_structure[
                    "context_single_label_row_share"
                ],
                "historical_capture_priority_candidate_id": capture_priority[
                    "top_priority_candidate_id"
                ],
                "historical_capture_priority_context_key": capture_priority[
                    "top_priority_context_key"
                ],
                "historical_uncovered_recommended_capture_candidate_ids": capture_priority[
                    "uncovered_recommended_candidate_ids"
                ],
                "current_capture_targets_all_covered": current_capture_targets_all_covered,
                "current_next_capture_priority_candidate_id": (
                    current_next_capture_priority_candidate_id
                ),
                "current_uncovered_recommended_capture_candidate_ids": (
                    current_uncovered_recommended_capture_candidate_ids
                ),
                "capture_priority_is_calibration_only": capture_priority[
                    "checks"
                ].get("priority_is_calibration_only"),
                "target_001_002_ready_case_count": target_001_002_replay[
                    "manifest_ready_case_count"
                ],
                "target_001_002_high_impact_candidate_count": (
                    target_001_002_replay["impact_high_impact_candidate_count"]
                ),
                "target_001_002_noop_candidate_count": target_001_002_replay[
                    "impact_noop_candidate_count"
                ],
                "tranq20_target_ready_case_count": tranq20_target_replay[
                    "manifest_ready_case_count"
                ],
                "tranq20_target_high_impact_candidate_count": (
                    tranq20_target_replay["impact_high_impact_candidate_count"]
                ),
            },
        },
        {
            "gate": "addition_before_selector",
            "current_status": (
                "calibrated_candidate_available"
                if has_replay_calibrated_selector_candidate
                else "failed_current_calibration"
            ),
            "passed_for_current_stage": has_replay_calibrated_selector_candidate,
            "evidence": {
                "legacy_exact_replay_single_feature_passing_count": (
                    replay_selector_passing_feature_count
                ),
                "legacy_exact_replay_pair_passing_holdout_gate_count": (
                    replay_pair_passing_holdout_gate_count
                ),
                "legacy_exact_replay_model_all_holdout_passing_count": len(
                    replay_model_selector_gate["all_holdout_passing_models"]
                ),
                "candidate_selector_passing_model_count": len(selector_passing_models),
                "target002_pt03_recovery": target002_pt03_recovery[
                    "check_target002_pt03_recovery_and_exact_replay"
                ],
                "with_target002_single_feature_passing_features": (
                    selector_gate_with_target002["passing_features_all_holdouts"]
                ),
                "with_target002_model_all_holdout_passing_models": (
                    selector_gate_with_target002["model_all_holdout_passing_models"]
                ),
                "with_target002_pair_no_all_holdout_rule": (
                    selector_gate_with_target002[
                        "pair_no_pair_rule_passes_all_holdout_gates"
                    ]
                ),
                "recommended_selector_candidate": (
                    replay_calibrated_selector_candidate[
                        "recommended_selector_candidate"
                    ]
                ),
                "recommended_selector_rule": (
                    replay_calibrated_selector_candidate[
                        "recommended_selector_rule"
                    ]
                ),
                "recommended_false_positive_count": (
                    replay_calibrated_selector_candidate[
                        "recommended_false_positive_count"
                    ]
                ),
                "recommended_false_negative_count": (
                    replay_calibrated_selector_candidate[
                        "recommended_false_negative_count"
                    ]
                ),
                "calibrated_selector_profile_smoke_ready": (
                    calibrated_selector_ab_profile_smoke[
                        "check_calibrated_selector_profile_smoke_is_wiring_only"
                    ]
                ),
                "has_robust_all_fold_feature_selector": (
                    has_robust_all_fold_feature_selector
                ),
                "has_robust_all_fold_model_selector": (
                    has_robust_all_fold_model_selector
                ),
                "has_robust_all_fold_rule_selector": (
                    has_robust_all_fold_rule_selector
                ),
                "has_robust_all_fold_selector": has_robust_all_fold_selector,
                "context_scalar_holdout_passing_model_count": (
                    selector_context_scalar_holdout.get("passing_model_count")
                ),
                "context_scalar_holdout_threshold_context_precision": (
                    selector_context_scalar_holdout.get(
                        "threshold_context_precision"
                    )
                ),
                "context_scalar_holdout_bin100_context_recall": (
                    selector_context_scalar_holdout.get("bin100_context_recall")
                ),
                "micro_vs_fold_robust_all_fold_passing_feature_count": (
                    selector_micro_vs_fold_gate.get(
                        "robust_all_fold_passing_feature_count"
                    )
                ),
                "micro_vs_fold_true_rc_context_passing_folds": (
                    f"{selector_micro_vs_fold_gate.get('true_rc_context_passing_fold_count')}/"
                    f"{selector_micro_vs_fold_gate.get('true_rc_context_fold_count')}"
                ),
                "micro_vs_fold_new_task_set_dataset_passing_folds": (
                    f"{selector_micro_vs_fold_gate.get('new_task_set_dataset_passing_fold_count')}/"
                    f"{selector_micro_vs_fold_gate.get('new_task_set_dataset_fold_count')}"
                ),
                "model_micro_vs_fold_robust_all_fold_passing_model_count": (
                    selector_model_micro_vs_fold_gate.get(
                        "robust_all_fold_passing_model_count"
                    )
                ),
                "model_micro_vs_fold_nearest_context_passing_folds": (
                    f"{selector_model_micro_vs_fold_gate.get('nearest_context_passing_fold_count')}/"
                    f"{selector_model_micro_vs_fold_gate.get('nearest_context_fold_count')}"
                ),
                "model_micro_vs_fold_shallow_dataset_passing_folds": (
                    f"{selector_model_micro_vs_fold_gate.get('shallow_dataset_passing_fold_count')}/"
                    f"{selector_model_micro_vs_fold_gate.get('shallow_dataset_fold_count')}"
                ),
                "rule_family_rule_count": selector_rule_family_search.get(
                    "rule_count"
                ),
                "rule_family_material_all_fold_passing_rule_count": (
                    selector_rule_family_search.get(
                        "material_all_fold_passing_rule_count"
                    )
                ),
                "rule_family_20only_rule_count": (
                    selector_rule_family_search_20only.get("rule_count")
                ),
                "rule_family_20only_material_all_fold_passing_rule_count": (
                    selector_rule_family_search_20only.get(
                        "material_all_fold_passing_rule_count"
                    )
                ),
                "rule_family_train_context_material_passing_folds": (
                    f"{selector_rule_family_train_holdout.get('context_material_passing_fold_count')}/"
                    f"{selector_rule_family_train_holdout.get('context_fold_count')}"
                ),
                "rule_family_train_20only_context_material_passing_folds": (
                    f"{selector_rule_family_train_holdout_20only.get('context_material_passing_fold_count')}/"
                    f"{selector_rule_family_train_holdout_20only.get('context_fold_count')}"
                ),
                "context_fold_anatomy_twenty_false_positive_no_positive_context_count": (
                    selector_context_fold_anatomy.get(
                        "twenty_false_positive_no_positive_context_count"
                    )
                ),
                "context_fold_anatomy_twenty_missed_positive_context_count": (
                    selector_context_fold_anatomy.get(
                        "twenty_missed_positive_context_count"
                    )
                ),
                "context_feature_mixed_instance_group_count": (
                    selector_context_feature_anatomy.get(
                        "mixed_instance_group_count"
                    )
                ),
                "context_feature_mixed_dataset_group_count": (
                    selector_context_feature_anatomy.get(
                        "mixed_dataset_group_count"
                    )
                ),
                "production_validated_selector": has_production_validated_selector,
            },
        },
        {
            "gate": "production_candidate_ab",
            "current_status": (
                "passed"
                if production_direction_proven
                else "blocked_until_production_selector_and_20_speedup_pass"
            ),
            "passed_for_current_stage": production_direction_proven,
            "evidence": {
                "has_small_no_regression_guard": has_small_no_regression_guard,
                "has_task5_noop_no_regression_guard": (
                    has_task5_noop_no_regression_guard
                ),
                "has_task10_noop_no_regression_guard": (
                    has_task10_noop_no_regression_guard
                ),
                "has_full_5_10_production_ab_evidence": (
                    has_full_5_10_production_ab_evidence
                ),
                "has_replay_calibrated_selector_candidate": (
                    has_replay_calibrated_selector_candidate
                ),
                "has_production_validated_selector": (
                    has_production_validated_selector
                ),
                "has_20_walltime_speedup_evidence": has_20_walltime_speedup_evidence,
                "calibrated_selector_smoke_twenty_worker_triggered_count": (
                    calibrated_selector_ab_profile_smoke[
                        "twenty_profile_worker_triggered_count"
                    ]
                ),
                "phase7o_all_time_limit": phase7o["all_time_limit"],
                "phase8q_all_time_limit": phase8q["all_time_limit"],
            },
        },
    )
    metrics = {
        "completion_requirements": {
            "has_small_no_regression_guard": has_small_no_regression_guard,
            "has_task5_noop_no_regression_guard": (
                has_task5_noop_no_regression_guard
            ),
            "has_task10_noop_no_regression_guard": (
                has_task10_noop_no_regression_guard
            ),
            "has_task10_triggered_regression_evidence": (
                has_task10_triggered_regression_evidence
            ),
            "has_full_5_10_production_ab_evidence": (
                has_full_5_10_production_ab_evidence
            ),
            "has_20_negative_columns": has_20_negative_columns,
            "has_local_rmp_impact": has_local_rmp_impact,
            "has_noop_counterexample": has_noop_counterexample,
            "has_legacy_selector_rejection_evidence": (
                has_legacy_selector_rejection_evidence
            ),
            "has_replay_calibrated_selector_candidate": (
                has_replay_calibrated_selector_candidate
            ),
            "has_robust_all_fold_feature_selector": (
                has_robust_all_fold_feature_selector
            ),
            "has_robust_all_fold_model_selector": (
                has_robust_all_fold_model_selector
            ),
            "has_robust_all_fold_rule_selector": (
                has_robust_all_fold_rule_selector
            ),
            "has_robust_all_fold_selector": has_robust_all_fold_selector,
            "has_production_validated_selector": has_production_validated_selector,
            "has_multi_context_clean_replay_calibration": (
                has_multi_context_clean_replay_calibration
            ),
            "has_20_walltime_speedup_evidence": has_20_walltime_speedup_evidence,
            "production_direction_proven": production_direction_proven,
        },
        "missing_requirements": missing_requirements,
        "next_evidence_gates": next_evidence_gates,
        "next_evidence_protocol": next_evidence_protocol,
        "next_evidence_protocol_readiness": next_evidence_protocol_readiness,
        "evidence_counts": {
            "small_triggered_worse_count": small["triggered_worse_count"],
            "small_nontriggered_official_changed": current_small[
                "nontriggered_official_changed"
            ],
            "phase8q_added_journeys": phase8q["pulse_worker_added_journeys"],
            "phase8q_added_new_task_sets": phase8q[
                "pulse_worker_added_new_task_set_count"
            ],
            "clean_replay_high_impact_candidate_count": real_capture[
                "high_impact_candidate_count"
            ],
            "clean_replay_noop_candidate_count": duplicate_noop["noop_candidate_count"],
            "combined_replay_candidate_row_count": combined["candidate_row_count"],
            "capture_expansion_event_count": replay_expansion["capture_event_count"],
            "capture_expansion_state_cap_tail_count": replay_expansion[
                "state_cap_tail_count"
            ],
            "global_capture_scan_event_count": global_capture_scan[
                "capture_event_count"
            ],
            "global_capture_scan_ready_20_context_count": global_capture_scan[
                "ready_20_context_count"
            ],
            "global_capture_scan_nonready_missing_vehicle_count": (
                global_capture_scan["nonready_missing_vehicle_count"]
            ),
            "clean_replay_context_family_count": clean_replay_context_family_count,
            "replay_candidate_count": candidate_capture_gap["candidate_count"],
            "replay_recommended_candidate_count": candidate_capture_gap[
                "recommended_candidate_count"
            ],
            "replay_candidate_to_ready_20_context_gap": candidate_capture_gap[
                "recommended_candidate_minus_ready_20_context_count"
            ],
            "counterfactual_capture_target_count": capture_targets["target_count"],
            "counterfactual_capture_exact_context_count": capture_targets[
                "exact_context_count"
            ],
            "counterfactual_capture_target_coverage_event_count": target_coverage[
                "capture_event_count"
            ],
            "counterfactual_capture_target_near_match_count": target_coverage[
                "target_with_near_match_count"
            ],
            "counterfactual_capture_target_exact_coverage_count": target_coverage[
                "target_with_exact_capture_count"
            ],
            "counterfactual_capture_target_uncovered_count": target_coverage[
                "uncovered_target_count"
            ],
            "current_capture_target_coverage_event_count": (
                target002_pt03_recovery["coverage_capture_event_count"]
            ),
            "current_capture_target_exact_coverage_count": (
                target002_pt03_recovery["coverage_target_with_exact_capture_count"]
            ),
            "current_capture_target_uncovered_count": (
                target002_pt03_recovery["coverage_uncovered_target_count"]
            ),
            "current_capture_targets_all_covered": target002_pt03_recovery[
                "check_target002_pt03_recovery_and_exact_replay"
            ],
            "counterfactual_tranq20_target_ready_case_count": tranq20_target_replay[
                "manifest_ready_case_count"
            ],
            "counterfactual_tranq20_target_high_impact_candidate_count": (
                tranq20_target_replay["impact_high_impact_candidate_count"]
            ),
            "counterfactual_tranq20_target_best_objective_delta": (
                tranq20_target_replay["impact_best_objective_delta"]
            ),
            "counterfactual_target_001_002_ready_case_count": (
                target_001_002_replay["manifest_ready_case_count"]
            ),
            "counterfactual_target_001_002_high_impact_candidate_count": (
                target_001_002_replay["impact_high_impact_candidate_count"]
            ),
            "counterfactual_target_001_002_noop_candidate_count": (
                target_001_002_replay["impact_noop_candidate_count"]
            ),
            "counterfactual_target_001_002_best_objective_delta": (
                target_001_002_replay["impact_best_objective_delta"]
            ),
            "counterfactual_target002_reproduction_gap_confirmed": target002_gap[
                "check_target002_gap_is_cg1_trajectory_drift"
            ],
            "counterfactual_target002_pt03_recovery_confirmed": (
                target002_pt03_recovery[
                    "check_target002_pt03_recovery_and_exact_replay"
                ]
            ),
            "counterfactual_target002_pt03_impact_candidate_row_count": (
                target002_pt03_recovery["impact_candidate_row_count"]
            ),
            "counterfactual_target002_pt03_high_impact_candidate_count": (
                target002_pt03_recovery["impact_high_impact_candidate_count"]
            ),
            "counterfactual_target002_pt03_noop_candidate_count": (
                target002_pt03_recovery["impact_noop_candidate_count"]
            ),
            "counterfactual_target002_pt03_best_objective_delta": (
                target002_pt03_recovery["impact_best_objective_delta"]
            ),
            "counterfactual_replay_selector_gate_row_count": replay_selector_gate[
                "row_count"
            ],
            "counterfactual_replay_selector_gate_label_improved": (
                replay_selector_gate["label_counts"].get("improved")
            ),
            "counterfactual_replay_selector_gate_label_noop": (
                replay_selector_gate["label_counts"].get("noop")
            ),
            "counterfactual_replay_selector_gate_full_true_rc_precision": (
                replay_selector_gate["full_sample_true_rc"]["precision"]
            ),
            "counterfactual_replay_selector_gate_full_true_rc_recall": (
                replay_selector_gate["full_sample_true_rc"]["recall"]
            ),
            "counterfactual_replay_selector_gate_dataset_true_rc_precision": (
                replay_selector_gate["dataset_holdout_true_rc"]["precision"]
            ),
            "counterfactual_replay_selector_gate_dataset_true_rc_recall": (
                replay_selector_gate["dataset_holdout_true_rc"]["recall"]
            ),
            "counterfactual_replay_selector_gate_train_best_dataset_precision": (
                replay_selector_gate["dataset_holdout_train_best"]["precision"]
            ),
            "counterfactual_replay_selector_gate_passing_feature_count": (
                replay_selector_passing_feature_count
            ),
            "counterfactual_replay_pair_selector_full_precision": (
                replay_pair_selector_gate["full_sample_best_pair"]["metrics"]["precision"]
            ),
            "counterfactual_replay_pair_selector_full_recall": (
                replay_pair_selector_gate["full_sample_best_pair"]["metrics"]["recall"]
            ),
            "counterfactual_replay_pair_selector_context_precision": (
                replay_pair_selector_gate["context_holdout_pair"]["precision"]
            ),
            "counterfactual_replay_pair_selector_context_recall": (
                replay_pair_selector_gate["context_holdout_pair"]["recall"]
            ),
            "counterfactual_replay_pair_selector_instance_precision": (
                replay_pair_selector_gate["instance_holdout_pair"]["precision"]
            ),
            "counterfactual_replay_pair_selector_instance_recall": (
                replay_pair_selector_gate["instance_holdout_pair"]["recall"]
            ),
            "counterfactual_replay_pair_selector_dataset_precision": (
                replay_pair_selector_gate["dataset_holdout_pair"]["precision"]
            ),
            "counterfactual_replay_pair_selector_dataset_recall": (
                replay_pair_selector_gate["dataset_holdout_pair"]["recall"]
            ),
            "counterfactual_replay_pair_selector_passing_holdout_gate_count": (
                replay_pair_passing_holdout_gate_count
            ),
            "counterfactual_replay_model_selector_context_passing_count": len(
                replay_model_selector_gate["context_passing_models"]
            ),
            "counterfactual_replay_model_selector_instance_passing_count": len(
                replay_model_selector_gate["instance_passing_models"]
            ),
            "counterfactual_replay_model_selector_dataset_passing_count": len(
                replay_model_selector_gate["dataset_passing_models"]
            ),
            "counterfactual_replay_model_selector_all_holdout_passing_count": len(
                replay_model_selector_gate["all_holdout_passing_models"]
            ),
            "counterfactual_replay_selector_gate_with_target002_row_count": (
                selector_gate_with_target002["row_count"]
            ),
            "counterfactual_replay_selector_gate_with_target002_label_improved": (
                selector_gate_with_target002["label_counts"].get("improved")
            ),
            "counterfactual_replay_selector_gate_with_target002_label_noop": (
                selector_gate_with_target002["label_counts"].get("noop")
            ),
            "counterfactual_replay_selector_gate_with_target002_passing_feature_count": (
                len(selector_gate_with_target002["passing_features_all_holdouts"])
            ),
            "counterfactual_replay_model_selector_with_target002_all_holdout_passing_count": (
                len(selector_gate_with_target002["model_all_holdout_passing_models"])
            ),
            "micro_vs_fold_robust_all_fold_passing_feature_count": (
                selector_micro_vs_fold_gate.get(
                    "robust_all_fold_passing_feature_count"
                )
            ),
            "model_micro_vs_fold_robust_all_fold_passing_model_count": (
                selector_model_micro_vs_fold_gate.get(
                    "robust_all_fold_passing_model_count"
                )
            ),
            "replay_local_selector_candidates_are_not_production": (
                bool(selector_gate_with_target002["passing_features_all_holdouts"])
                and bool(
                    selector_gate_with_target002["model_all_holdout_passing_models"]
                )
                and not has_robust_all_fold_selector
                and not has_production_validated_selector
            ),
            "replay_calibrated_selector_candidate": (
                replay_calibrated_selector_candidate[
                    "recommended_selector_candidate"
                ]
            ),
            "replay_calibrated_selector_full_precision": (
                replay_calibrated_selector_candidate["recommended_full_sample"][
                    "precision"
                ]
            ),
            "replay_calibrated_selector_full_recall": (
                replay_calibrated_selector_candidate["recommended_full_sample"][
                    "recall"
                ]
            ),
            "replay_calibrated_selector_false_positive_count": (
                replay_calibrated_selector_candidate[
                    "recommended_false_positive_count"
                ]
            ),
            "replay_calibrated_selector_false_negative_count": (
                replay_calibrated_selector_candidate[
                    "recommended_false_negative_count"
                ]
            ),
            "replay_calibrated_selector_selected_only_noop_case_count": (
                replay_calibrated_selector_candidate["recommended_case_level"][
                    "selected_only_noop"
                ]
            ),
            "replay_calibrated_selector_missed_positive_case_count": (
                replay_calibrated_selector_candidate["recommended_case_level"][
                    "missed_positive_case"
                ]
            ),
            "calibrated_selector_smoke_small_worker_events": (
                calibrated_selector_ab_profile_smoke["small_profile_worker_events"]
            ),
            "calibrated_selector_smoke_twenty_worker_events": (
                calibrated_selector_ab_profile_smoke["twenty_profile_worker_events"]
            ),
            "calibrated_selector_smoke_twenty_pricing_states": (
                calibrated_selector_ab_profile_smoke["twenty_profile_pricing_states"]
            ),
            "counterfactual_replay_dataset_structure_dataset_mixed_label_group_count": (
                replay_dataset_structure["dataset_mixed_label_group_count"]
            ),
            "counterfactual_replay_dataset_structure_context_mixed_label_group_count": (
                replay_dataset_structure["context_mixed_label_group_count"]
            ),
            "counterfactual_replay_dataset_structure_context_single_label_row_share": (
                replay_dataset_structure["context_single_label_row_share"]
            ),
            "historical_counterfactual_capture_priority_top_candidate_id": capture_priority[
                "top_priority_candidate_id"
            ],
            "historical_counterfactual_capture_priority_top_context_key": capture_priority[
                "top_priority_context_key"
            ],
            "historical_counterfactual_capture_priority_uncovered_recommended_candidate_ids": (
                capture_priority["uncovered_recommended_candidate_ids"]
            ),
            "current_next_capture_priority_candidate_id": (
                current_next_capture_priority_candidate_id
            ),
            "current_uncovered_recommended_capture_candidate_ids": (
                current_uncovered_recommended_capture_candidate_ids
            ),
            "selector_passing_model_count": len(selector_passing_models),
            "phase7o_worker_rows": phase7o["rows"],
            "phase8q_worker_rows": phase8q["rows"],
        },
        "selector_gate": {
            "passing_models": selector_passing_models,
            "pre_batch_leave_one_dataset_precision": pre_batch_lod["precision"],
            "pre_batch_leave_one_dataset_recall": pre_batch_lod["recall"],
            "pre_batch_leave_one_instance_precision": pre_batch_loi["precision"],
            "pre_batch_leave_one_instance_recall": pre_batch_loi["recall"],
            "exact_replay_passing_features_all_holdouts": replay_selector_gate[
                "passing_features_all_holdouts"
            ],
            "exact_replay_full_sample_true_rc": replay_selector_gate[
                "full_sample_true_rc"
            ],
            "exact_replay_dataset_holdout_true_rc": replay_selector_gate[
                "dataset_holdout_true_rc"
            ],
            "exact_replay_dataset_holdout_train_best": replay_selector_gate[
                "dataset_holdout_train_best"
            ],
            "exact_replay_full_sample_best_pair": replay_pair_selector_gate[
                "full_sample_best_pair"
            ],
            "exact_replay_pair_context_holdout": replay_pair_selector_gate[
                "context_holdout_pair"
            ],
            "exact_replay_pair_instance_holdout": replay_pair_selector_gate[
                "instance_holdout_pair"
            ],
            "exact_replay_pair_dataset_holdout": replay_pair_selector_gate[
                "dataset_holdout_pair"
            ],
            "exact_replay_model_context_passing_models": replay_model_selector_gate[
                "context_passing_models"
            ],
            "exact_replay_model_instance_passing_models": replay_model_selector_gate[
                "instance_passing_models"
            ],
            "exact_replay_model_dataset_passing_models": replay_model_selector_gate[
                "dataset_passing_models"
            ],
            "exact_replay_model_all_holdout_passing_models": (
                replay_model_selector_gate["all_holdout_passing_models"]
            ),
            "exact_replay_model_dataset_models": replay_model_selector_gate[
                "dataset_models"
            ],
            "with_target002_passing_features_all_holdouts": (
                selector_gate_with_target002["passing_features_all_holdouts"]
            ),
            "with_target002_pair_no_pair_rule_passes_all_holdout_gates": (
                selector_gate_with_target002[
                    "pair_no_pair_rule_passes_all_holdout_gates"
                ]
            ),
            "with_target002_model_all_holdout_passing_models": (
                selector_gate_with_target002["model_all_holdout_passing_models"]
            ),
            "recommended_replay_calibrated_selector": (
                replay_calibrated_selector_candidate[
                    "recommended_selector_candidate"
                ]
            ),
            "recommended_replay_calibrated_rule": (
                replay_calibrated_selector_candidate[
                    "recommended_selector_rule"
                ]
            ),
            "recommended_replay_calibrated_full_sample": (
                replay_calibrated_selector_candidate["recommended_full_sample"]
            ),
            "recommended_replay_calibrated_case_level": (
                replay_calibrated_selector_candidate["recommended_case_level"]
            ),
        },
        "interpretation": (
            "Root-cause evidence is strong, but the production optimization direction "
            "is not proven: clean replay calibration now spans more than one 20-task "
            "context family, target002/priority capture shows exact target contexts "
            "are not reliably recovered under current config-matched reruns, and exact "
            "replay selector-gate rows now expose calibrated addition-before "
            "candidates. Those candidates are only calibration evidence until context, "
            "instance, and dataset holdouts pass and then full BPC A/B proves 5/10 "
            "no-regression plus selected 20-task speedup."
        ),
    }
    metrics["check_root_cause_known_but_optimization_direction_unproven"] = (
        has_small_no_regression_guard
        and has_20_negative_columns
        and has_local_rmp_impact
        and has_noop_counterexample
        and has_replay_calibrated_selector_candidate
        and not has_production_validated_selector
        and not has_20_walltime_speedup_evidence
        and not production_direction_proven
    )
    return metrics


def _goal_completion_audit_metrics(checks: dict[str, Any]) -> dict[str, Any]:
    readiness = checks["optimization_direction_readiness"]
    requirements = readiness["completion_requirements"]
    missing_requirements = list(readiness["missing_requirements"])
    missing_requirement_names = [
        str(item.get("requirement", "")) for item in missing_requirements
    ]
    expected_missing_requirements = [
        "five_ten_full_no_regression_ab",
        "production_validated_selector",
        "twenty_walltime_speedup",
    ]
    stable_document_claim_evidence = {
        "readiness_semantics_current": readiness[
            "check_root_cause_known_but_optimization_direction_unproven"
        ],
        "final_synthesis_report_current": checks["final_report"][
            "check_final_synthesis_report_is_current"
        ],
        "requirement_audit_report_current": checks["requirement_audit_report"][
            "check_requirement_audit_report_is_current"
        ],
        "optimization_direction_readiness_report_current": checks[
            "optimization_direction_readiness_report"
        ]["check_optimization_direction_readiness_report_is_current"],
        "root_cause_diagnosis_report_current": checks["root_cause_diagnosis_report"][
            "check_root_cause_diagnosis_report_is_current"
        ],
        "goal_completion_blockers_report_current": checks[
            "goal_completion_blockers_report"
        ]["check_goal_completion_blockers_report_is_current"],
        "goal_current_summary_current": checks["goal_current_summary"][
            "check_goal_current_summary_is_current"
        ],
        "missing_requirements_match_expected": (
            missing_requirement_names == expected_missing_requirements
        ),
        "completion_decision_should_stay_active": (
            not requirements["production_direction_proven"]
            and not requirements["has_production_validated_selector"]
            and not requirements["has_20_walltime_speedup_evidence"]
        ),
    }
    stable_document_claims_consistent = bool(
        all(stable_document_claim_evidence.values())
    )
    root_cause_evidence_proved = bool(stable_document_claims_consistent)
    not_pulse_only_evidence = {
        "small_scale_overhead": checks["small_scale_overhead"][
            "check_triggered_all_worse"
        ],
        "worker_add_column_not_sufficient": checks["phase8q_worker_add_columns"][
            "check_worker_can_add_but_not_solve"
        ],
        "candidate_batch_selector_not_stable": checks["candidate_batch_selector"][
            "check_candidate_batch_selector_not_stable"
        ],
        "exact_replay_has_high_impact_and_noop": (
            checks["counterfactual_replay_impact_dataset"][
                "check_impact_dataset_separates_high_impact_and_noop"
            ]
        ),
        "real_capture_local_rmp_impact": checks["counterfactual_replay_real_capture"][
            "check_real_capture_replay_has_local_rmp_impact"
        ],
        "rule_family_rejects_simple_selectors": checks[
            "selector_rule_family_search"
        ]["check_rule_family_search_rejects_simple_conjunctions"],
        "context_feature_supports_rmp_trajectory": checks[
            "selector_context_feature_anatomy"
        ]["check_context_feature_anatomy_supports_context_root_cause"],
        "failure_matrix_routes_have_evidence": checks["root_cause_failure_matrix"][
            "check_failure_matrix_routes_have_evidence"
        ],
        "code_boundary_no_unvalidated_production_effect": checks[
            "root_cause_code_boundary"
        ]["check_code_boundary_no_unvalidated_production_effect"],
    }
    not_pulse_only_proved = bool(
        all(not_pulse_only_evidence.values())
    )
    no_unvalidated_mainline_change_evidence = {
        "counterfactual_capture_guarded_by_config": checks[
            "root_cause_code_boundary"
        ]["counterfactual_capture_guarded_by_config"],
        "counterfactual_capture_default_enabled": checks[
            "root_cause_code_boundary"
        ]["counterfactual_capture_default_enabled"],
        "counterfactual_capture_diagnostic_only": checks[
            "root_cause_code_boundary"
        ]["counterfactual_capture_diagnostic_only"],
        "counterfactual_capture_certificate_capable": checks[
            "root_cause_code_boundary"
        ]["counterfactual_capture_certificate_capable"],
        "counterfactual_capture_official_bound_effect": checks[
            "root_cause_code_boundary"
        ]["counterfactual_capture_official_bound_effect"],
        "profile_priority_defaults_empty": checks["root_cause_code_boundary"][
            "profile_priority_defaults_empty"
        ],
        "mainline_unvalidated_effect_default_enabled": checks[
            "root_cause_code_boundary"
        ]["mainline_unvalidated_effect_default_enabled"],
        "code_boundary_check": checks["root_cause_code_boundary"][
            "check_code_boundary_no_unvalidated_production_effect"
        ],
    }
    no_unvalidated_mainline_change_proved = bool(
        no_unvalidated_mainline_change_evidence[
            "counterfactual_capture_guarded_by_config"
        ]
        and no_unvalidated_mainline_change_evidence[
            "counterfactual_capture_default_enabled"
        ]
        is False
        and no_unvalidated_mainline_change_evidence[
            "counterfactual_capture_diagnostic_only"
        ]
        and no_unvalidated_mainline_change_evidence[
            "counterfactual_capture_certificate_capable"
        ]
        is False
        and no_unvalidated_mainline_change_evidence[
            "counterfactual_capture_official_bound_effect"
        ]
        is False
        and no_unvalidated_mainline_change_evidence["profile_priority_defaults_empty"]
        and no_unvalidated_mainline_change_evidence[
            "mainline_unvalidated_effect_default_enabled"
        ]
        is False
        and no_unvalidated_mainline_change_evidence["code_boundary_check"]
    )
    production_direction_proved = bool(requirements["production_direction_proven"])
    exact_5_10_20_optimization_proved = bool(
        requirements["has_small_no_regression_guard"]
        and requirements["has_task5_noop_no_regression_guard"]
        and requirements["has_task10_noop_no_regression_guard"]
        and requirements["has_full_5_10_production_ab_evidence"]
        and requirements["has_20_walltime_speedup_evidence"]
        and production_direction_proved
    )
    unproven_experiment_evidence = {
        "worker_can_add_negative_columns": requirements["has_20_negative_columns"],
        "local_rmp_impact_exists": requirements["has_local_rmp_impact"],
        "replay_calibrated_selector_candidate_exists": requirements[
            "has_replay_calibrated_selector_candidate"
        ],
        "worker_add_columns_did_not_solve": checks["phase8q_worker_add_columns"][
            "check_worker_can_add_but_not_solve"
        ],
        "exact_replay_has_high_impact_and_noop": (
            checks["counterfactual_replay_impact_dataset"][
                "check_impact_dataset_separates_high_impact_and_noop"
            ]
        ),
        "production_selector_missing": not requirements[
            "has_production_validated_selector"
        ],
        "twenty_walltime_speedup_missing": not requirements[
            "has_20_walltime_speedup_evidence"
        ],
        "production_direction_not_proven": not production_direction_proved,
    }
    unproven_experiments_not_counted_as_completion = bool(
        all(unproven_experiment_evidence.values())
    )
    five_ten_noop_guard_evidence = {
        "task5_noop_guard_no_official_change": requirements[
            "has_task5_noop_no_regression_guard"
        ],
        "task10_noop_guard_no_official_change": requirements[
            "has_task10_noop_no_regression_guard"
        ],
        "task10_triggered_regression_risk": requirements[
            "has_task10_triggered_regression_evidence"
        ],
        "task10_triggered": checks["current_small_summary_scan"]["task10_triggered"],
        "full_5_10_production_ab_evidence": requirements[
            "has_full_5_10_production_ab_evidence"
        ],
    }
    five_ten_noop_guard_not_worker_success = bool(
        five_ten_noop_guard_evidence["task5_noop_guard_no_official_change"]
        and five_ten_noop_guard_evidence["task10_noop_guard_no_official_change"]
        and five_ten_noop_guard_evidence["task10_triggered_regression_risk"]
        and five_ten_noop_guard_evidence["full_5_10_production_ab_evidence"]
        is False
    )
    audit_items = [
        {
            "requirement": "root_cause_explanation_has_evidence",
            "status": "proved" if root_cause_evidence_proved else "not_proved",
            "evidence": (
                "Diagnosis report, final synthesis, requirement audit, and evidence "
                "ledger all agree on the current root-cause explanation."
            ),
            "details": stable_document_claim_evidence,
        },
        {
            "requirement": "not_limited_to_pulse",
            "status": "proved" if not_pulse_only_proved else "not_proved",
            "evidence": not_pulse_only_evidence,
        },
        {
            "requirement": "no_unvalidated_mainline_change_before_proof",
            "status": (
                "proved"
                if no_unvalidated_mainline_change_proved
                else "not_proved"
            ),
            "evidence": no_unvalidated_mainline_change_evidence,
        },
        {
            "requirement": "unproven_experiments_not_counted_as_completion",
            "status": (
                "proved"
                if unproven_experiments_not_counted_as_completion
                else "not_proved"
            ),
            "evidence": unproven_experiment_evidence,
        },
        {
            "requirement": "five_ten_no_regression_is_noop_guard_not_worker_success",
            "status": (
                "proved" if five_ten_noop_guard_not_worker_success else "not_proved"
            ),
            "evidence": five_ten_noop_guard_evidence,
        },
        {
            "requirement": "stable_production_optimization_direction",
            "status": "proved" if production_direction_proved else "not_proved",
            "evidence": requirements,
        },
        {
            "requirement": "exact_5_10_no_regression_and_20_speedup",
            "status": (
                "proved" if exact_5_10_20_optimization_proved else "not_proved"
            ),
            "evidence": {
                "has_small_no_regression_guard": requirements[
                    "has_small_no_regression_guard"
                ],
                "has_task5_noop_no_regression_guard": requirements[
                    "has_task5_noop_no_regression_guard"
                ],
                "has_task10_noop_no_regression_guard": requirements[
                    "has_task10_noop_no_regression_guard"
                ],
                "has_full_5_10_production_ab_evidence": requirements[
                    "has_full_5_10_production_ab_evidence"
                ],
                "has_20_walltime_speedup_evidence": requirements[
                    "has_20_walltime_speedup_evidence"
                ],
                "production_direction_proven": production_direction_proved,
            },
        },
    ]
    goal_complete = bool(
        root_cause_evidence_proved
        and not_pulse_only_proved
        and no_unvalidated_mainline_change_proved
        and unproven_experiments_not_counted_as_completion
        and five_ten_noop_guard_not_worker_success
        and production_direction_proved
        and exact_5_10_20_optimization_proved
        and not missing_requirements
    )
    return {
        "goal_complete": goal_complete,
        "should_mark_goal_complete": goal_complete,
        "audit_items": audit_items,
        "blocking_missing_requirements": missing_requirements,
        "stable_document_claim_evidence": stable_document_claim_evidence,
        "stable_document_claims_consistent": stable_document_claims_consistent,
        "check_goal_completion_audit_is_consistent": bool(
            root_cause_evidence_proved
            and not_pulse_only_proved
            and no_unvalidated_mainline_change_proved
            and unproven_experiments_not_counted_as_completion
            and not goal_complete
            and bool(missing_requirements)
            and not production_direction_proved
        ),
    }


def build_evidence_ledger() -> dict[str, Any]:
    checks = {
        "small_scale_overhead": _small_scale_report_metrics(SMALL_REPORT),
        "current_small_summary_scan": _current_small_summary_scan_metrics(RESULTS_DIR),
        "phase7o_worker_roi": _phase7o_metrics(PHASE7O_SUMMARY),
        "phase8q_worker_add_columns": _phase8q_metrics(PHASE8Q_SUMMARY),
        "candidate_batch_selector": _candidate_summary_metrics(CANDIDATE_SUMMARY),
        "candidate_selector_models": _candidate_model_metrics(CANDIDATE_MODEL_SUMMARY),
        "selector_failure_anatomy": _selector_failure_metrics(SELECTOR_FAILURE_SUMMARY),
        "hindsight_oracle_gap": _hindsight_oracle_gap_metrics(HINDSIGHT_ORACLE_GAP_SUMMARY),
        "candidate_label_granularity": _candidate_label_granularity_metrics(
            CANDIDATE_LABEL_GRANULARITY_SUMMARY
        ),
        "batch_level_selector": _batch_level_selector_metrics(BATCH_LEVEL_SELECTOR_SUMMARY),
        "trajectory_signal_ladder": _trajectory_signal_ladder_metrics(
            TRAJECTORY_SIGNAL_LADDER_SUMMARY
        ),
        "batch_gate_stability": _batch_gate_stability_metrics(BATCH_GATE_STABILITY_SUMMARY),
        "context_stratification": _context_stratification_metrics(
            CONTEXT_STRATIFICATION_SUMMARY
        ),
        "context_only_baseline": _context_only_baseline_metrics(
            CONTEXT_ONLY_BASELINE_SUMMARY
        ),
        "matched_context_audit": _matched_context_audit_metrics(
            MATCHED_CONTEXT_AUDIT_SUMMARY
        ),
        "matched_context_pairwise": _matched_context_pairwise_metrics(
            MATCHED_CONTEXT_PAIRWISE_SUMMARY
        ),
        "exact_context_label_conflicts": _exact_context_label_conflict_metrics(
            EXACT_CONTEXT_LABEL_CONFLICTS_SUMMARY
        ),
        "counterfactual_replay_coverage": _counterfactual_replay_coverage_metrics(
            COUNTERFACTUAL_REPLAY_COVERAGE_SUMMARY
        ),
        "counterfactual_replay_candidates": _counterfactual_replay_candidate_metrics(
            COUNTERFACTUAL_REPLAY_CANDIDATES_SUMMARY
        ),
        "counterfactual_replay_readiness": _counterfactual_replay_readiness_metrics(
            COUNTERFACTUAL_REPLAY_READINESS_SUMMARY
        ),
        "counterfactual_replay_materialization": (
            _counterfactual_replay_materialization_metrics(
                COUNTERFACTUAL_REPLAY_MATERIALIZATION_SUMMARY
            )
        ),
        "counterfactual_replay_capture_smoke": (
            _counterfactual_replay_capture_smoke_metrics(
                COUNTERFACTUAL_REPLAY_CAPTURE_SMOKE_SUMMARY
            )
        ),
        "counterfactual_replay_manifest_smoke": (
            _counterfactual_replay_manifest_smoke_metrics(
                COUNTERFACTUAL_REPLAY_MANIFEST_SMOKE_SUMMARY
            )
        ),
        "counterfactual_replay_feasible_smoke": (
            _counterfactual_replay_feasible_smoke_metrics(
                COUNTERFACTUAL_REPLAY_FEASIBLE_SMOKE_SUMMARY
            )
        ),
        "counterfactual_replay_gap": _counterfactual_replay_gap_metrics(
            COUNTERFACTUAL_REPLAY_GAP_SUMMARY
        ),
        "counterfactual_replay_real_capture": _counterfactual_replay_real_capture_metrics(
            COUNTERFACTUAL_REPLAY_REAL_CAPTURE_AUDIT_SUMMARY,
            COUNTERFACTUAL_REPLAY_REAL_CAPTURE_MANIFEST_SUMMARY,
            COUNTERFACTUAL_REPLAY_REAL_CAPTURE_RESULT_SUMMARY,
        ),
        "counterfactual_replay_impact_dataset": (
            _counterfactual_replay_impact_dataset_metrics(
                COUNTERFACTUAL_REPLAY_IMPACT_REAL_CAPTURE_SUMMARY,
                COUNTERFACTUAL_REPLAY_IMPACT_DUPLICATE_NOOP_SUMMARY,
                COUNTERFACTUAL_REPLAY_IMPACT_COMBINED_SUMMARY,
            )
        ),
        "counterfactual_replay_payload_quality": (
            _counterfactual_replay_payload_quality_metrics(
                COUNTERFACTUAL_REPLAY_PAYLOAD_QUALITY_REPORT,
                COUNTERFACTUAL_REPLAY_PAYLOAD_QUALITY_AUDIT_SUMMARY,
                COUNTERFACTUAL_REPLAY_PAYLOAD_QUALITY_MANIFEST_SUMMARY,
                COUNTERFACTUAL_REPLAY_PAYLOAD_QUALITY_REPLAY_SUMMARY,
                COUNTERFACTUAL_REPLAY_PAYLOAD_QUALITY_IMPACT_SUMMARY,
            )
        ),
        "counterfactual_replay_capture_expansion": (
            _counterfactual_replay_capture_expansion_metrics(
                COUNTERFACTUAL_REPLAY_CAPTURE_EXPANSION_MT20_TRANQ_SUMMARY,
                COUNTERFACTUAL_REPLAY_CAPTURE_EXPANSION_MT20_TRANQ_AUDIT_SUMMARY,
                COUNTERFACTUAL_REPLAY_CAPTURE_EXPANSION_TRANQ20_01_SUMMARY,
                COUNTERFACTUAL_REPLAY_CAPTURE_EXPANSION_TRANQ20_01_AUDIT_SUMMARY,
            )
        ),
        "counterfactual_replay_global_capture_scan": (
            _counterfactual_replay_global_capture_scan_metrics(
                COUNTERFACTUAL_REPLAY_GLOBAL_CAPTURE_SCAN_REPORT,
                COUNTERFACTUAL_REPLAY_GLOBAL_CAPTURE_SCAN_AUDIT_SUMMARY,
                COUNTERFACTUAL_REPLAY_GLOBAL_CAPTURE_SCAN_MANIFEST,
                COUNTERFACTUAL_REPLAY_GLOBAL_CAPTURE_SCAN_MANIFEST_SUMMARY,
                COUNTERFACTUAL_REPLAY_GLOBAL_CAPTURE_SCAN_REPLAY_SUMMARY,
                COUNTERFACTUAL_REPLAY_GLOBAL_CAPTURE_SCAN_IMPACT_SUMMARY,
            )
        ),
    }
    checks["counterfactual_replay_candidate_to_capture_gap"] = (
        _counterfactual_replay_candidate_to_capture_gap_metrics(
            checks["counterfactual_replay_candidates"],
            checks["counterfactual_replay_global_capture_scan"],
            COUNTERFACTUAL_REPLAY_CANDIDATE_TO_CAPTURE_GAP_REPORT,
        )
    )
    checks["counterfactual_capture_targets"] = _counterfactual_capture_targets_metrics(
        COUNTERFACTUAL_CAPTURE_TARGETS_SUMMARY,
        COUNTERFACTUAL_CAPTURE_TARGETS_REPORT,
        checks["counterfactual_replay_candidate_to_capture_gap"],
    )
    checks["counterfactual_capture_target_coverage"] = (
        _counterfactual_capture_target_coverage_metrics(
            COUNTERFACTUAL_CAPTURE_TARGET_COVERAGE_SUMMARY,
            COUNTERFACTUAL_CAPTURE_TARGET_COVERAGE_REPORT,
            checks["counterfactual_capture_targets"],
        )
    )
    checks["counterfactual_target_tranq20_replay"] = (
        _counterfactual_target_tranq20_replay_metrics(
            COUNTERFACTUAL_TARGET_TRANQ20_REPLAY_REPORT,
            COUNTERFACTUAL_TARGET_TRANQ20_CAPTURE_AUDIT_SUMMARY,
            COUNTERFACTUAL_TARGET_TRANQ20_MANIFEST_SUMMARY,
            COUNTERFACTUAL_TARGET_TRANQ20_REPLAY_SUMMARY,
            COUNTERFACTUAL_TARGET_TRANQ20_IMPACT_SUMMARY,
        )
    )
    checks["counterfactual_target_001_002_replay"] = (
        _counterfactual_target_001_002_replay_metrics(
            COUNTERFACTUAL_TARGET_001_002_REPLAY_REPORT,
            COUNTERFACTUAL_TARGET_001_002_CAPTURE_AUDIT_SUMMARY,
            COUNTERFACTUAL_TARGET_001_002_MANIFEST_SUMMARY,
            COUNTERFACTUAL_TARGET_001_002_REPLAY_SUMMARY,
            COUNTERFACTUAL_TARGET_001_002_IMPACT_SUMMARY,
        )
    )
    checks["counterfactual_target002_reproduction_gap"] = (
        _target002_reproduction_gap_metrics(
            TARGET002_REPRODUCTION_GAP_REPORT,
            TARGET002_NO_CAPTURE_MIRROR_SUMMARY,
        )
    )
    checks["counterfactual_replay_selector_gate"] = (
        _counterfactual_replay_selector_gate_metrics(
            COUNTERFACTUAL_REPLAY_SELECTOR_GATE_SUMMARY
        )
    )
    checks["counterfactual_replay_pair_selector_gate"] = (
        _counterfactual_replay_pair_selector_gate_metrics(
            COUNTERFACTUAL_REPLAY_PAIR_SELECTOR_GATE_SUMMARY
        )
    )
    checks["counterfactual_replay_model_selector_gate"] = (
        _counterfactual_replay_model_selector_gate_metrics(
            COUNTERFACTUAL_REPLAY_MODEL_SELECTOR_GATE_SUMMARY
        )
    )
    checks["counterfactual_target002_pt03_recovery"] = (
        _target002_pt03_recovery_metrics(
            TARGET002_PT03_RECOVERY_REPORT,
            TARGET002_NO_CAPTURE_MIRROR_PT03_SUMMARY,
            COUNTERFACTUAL_CAPTURE_TARGET_COVERAGE_AFTER_TARGET002_PT03_SUMMARY,
            TARGET002_PT03_CAPTURE_AUDIT_SUMMARY,
            TARGET002_PT03_MANIFEST_SUMMARY,
            TARGET002_PT03_REPLAY_SUMMARY,
            TARGET002_PT03_IMPACT_SUMMARY,
        )
    )
    checks["counterfactual_replay_selector_gate_with_target002_pt03"] = (
        _selector_gate_with_target002_pt03_metrics(
            COUNTERFACTUAL_REPLAY_SELECTOR_GATE_WITH_TARGET002_PT03_SUMMARY,
            COUNTERFACTUAL_REPLAY_PAIR_SELECTOR_GATE_WITH_TARGET002_PT03_SUMMARY,
            COUNTERFACTUAL_REPLAY_MODEL_SELECTOR_GATE_WITH_TARGET002_PT03_SUMMARY,
        )
    )
    checks["replay_calibrated_selector_candidate"] = (
        _replay_calibrated_selector_candidate_metrics(
            REPLAY_CALIBRATED_SELECTOR_CANDIDATE_SUMMARY,
            REPLAY_CALIBRATED_SELECTOR_CANDIDATE_REPORT,
        )
    )
    checks["calibrated_selector_ab_profile_smoke"] = (
        _calibrated_selector_ab_profile_smoke_metrics(
            CALIBRATED_SELECTOR_AB_PROFILE_REPORT,
            CALIBRATED_SELECTOR_GATE_SMOKE_CSV,
            CALIBRATED_SELECTOR_MT20_APOLLO_SMOKE_CSV,
            CALIBRATED_SELECTOR_TRANQ20_SMOKE_CSV,
            CALIBRATED_SELECTOR_MT20_TRANQ_SMOKE_CSV,
        )
    )
    checks["calibrated_selector_hardtail_worker_smoke"] = (
        _calibrated_selector_hardtail_worker_smoke_metrics(
            CALIBRATED_SELECTOR_HARDTAIL_WORKER_REPORT,
            CALIBRATED_SELECTOR_HARDTAIL_WORKER_SMOKE_CSV,
        )
    )
    checks["calibrated_selector_hardtail_gate_smoke"] = (
        _calibrated_selector_hardtail_gate_smoke_metrics(
            CALIBRATED_SELECTOR_HARDTAIL_GATE_REPORT,
            CALIBRATED_SELECTOR_HARDTAIL_GATE_SMOKE_CSV,
        )
    )
    checks["calibrated_selector_hardtail_repeat_gate"] = (
        _calibrated_selector_hardtail_repeat_gate_metrics(
            CALIBRATED_SELECTOR_HARDTAIL_REPEAT_GATE_REPORT,
            CALIBRATED_SELECTOR_HARDTAIL_REPEAT_GATE_CSV,
        )
    )
    checks["calibrated_selector_selected20_repeat_ab"] = (
        _calibrated_selector_selected20_repeat_ab_metrics(
            CALIBRATED_SELECTOR_SELECTED20_REPEAT_AB_REPORT,
            CALIBRATED_SELECTOR_SELECTED20_REPEAT_AB_CSV,
        )
    )
    checks["counterfactual_replay_dataset_structure"] = (
        _counterfactual_replay_dataset_structure_metrics(
            COUNTERFACTUAL_REPLAY_DATASET_STRUCTURE_SUMMARY,
            COUNTERFACTUAL_REPLAY_DATASET_STRUCTURE_REPORT,
        )
    )
    checks["counterfactual_capture_priority"] = _counterfactual_capture_priority_metrics(
        COUNTERFACTUAL_CAPTURE_PRIORITY_SUMMARY,
        COUNTERFACTUAL_CAPTURE_PRIORITY_REPORT,
    )
    checks["final_report"] = _final_synthesis_report_metrics(FINAL_REPORT)
    checks["requirement_audit_report"] = _requirement_audit_report_metrics(
        REQUIREMENT_AUDIT_REPORT
    )
    checks["optimization_direction_readiness_report"] = (
        _optimization_direction_readiness_report_metrics(
            OPTIMIZATION_DIRECTION_READINESS_REPORT
        )
    )
    checks["root_cause_diagnosis_report"] = _root_cause_diagnosis_report_metrics(
        ROOT_CAUSE_DIAGNOSIS_REPORT
    )
    checks["goal_completion_blockers_report"] = (
        _goal_completion_blockers_report_metrics(
            GOAL_COMPLETION_BLOCKERS_REPORT
        )
    )
    checks["objective_completion_audit_catalog"] = (
        _objective_completion_audit_catalog_metrics(
            OBJECTIVE_COMPLETION_AUDIT_SUMMARY,
            OBJECTIVE_COMPLETION_AUDIT_REPORT,
        )
    )
    checks["next_evidence_protocol_catalog"] = (
        _next_evidence_protocol_catalog_metrics(
            NEXT_EVIDENCE_PROTOCOL_CATALOG_SUMMARY,
            NEXT_EVIDENCE_PROTOCOL_CATALOG_REPORT,
        )
    )
    checks["evidence_bundle_manifest"] = _evidence_bundle_manifest_metrics(
        EVIDENCE_BUNDLE_MANIFEST_SUMMARY,
        EVIDENCE_BUNDLE_MANIFEST_REPORT,
    )
    checks["evidence_bundle_rebuild"] = _evidence_bundle_rebuild_metrics(
        EVIDENCE_BUNDLE_REBUILD_SUMMARY,
        EVIDENCE_BUNDLE_REBUILD_REPORT,
    )
    checks["root_cause_current_answer"] = _root_cause_current_answer_metrics(
        ROOT_CAUSE_CURRENT_ANSWER_SUMMARY,
        ROOT_CAUSE_CURRENT_ANSWER_REPORT,
    )
    checks["root_cause_causal_chain_audit"] = (
        _root_cause_causal_chain_audit_metrics(
            ROOT_CAUSE_CAUSAL_CHAIN_AUDIT_SUMMARY,
            ROOT_CAUSE_CAUSAL_CHAIN_AUDIT_REPORT,
        )
    )
    checks["root_cause_stale_claims"] = _root_cause_stale_claims_metrics(
        ROOT_CAUSE_STALE_CLAIMS_SUMMARY,
        ROOT_CAUSE_STALE_CLAIMS_REPORT,
    )
    checks["root_cause_missing_requirement_evidence_scan"] = (
        _root_cause_missing_requirement_evidence_scan_metrics(
            ROOT_CAUSE_MISSING_REQUIREMENT_EVIDENCE_SCAN_SUMMARY,
            ROOT_CAUSE_MISSING_REQUIREMENT_EVIDENCE_SCAN_REPORT,
        )
    )
    checks["root_cause_next_action_plan"] = _root_cause_next_action_plan_metrics(
        ROOT_CAUSE_NEXT_ACTION_PLAN_SUMMARY,
        ROOT_CAUSE_NEXT_ACTION_PLAN_REPORT,
    )
    checks["root_cause_document_consistency"] = (
        _root_cause_document_consistency_metrics(
            ROOT_CAUSE_DOCUMENT_CONSISTENCY_SUMMARY,
            ROOT_CAUSE_DOCUMENT_CONSISTENCY_REPORT,
        )
    )
    checks["root_cause_selector_collection_plan"] = (
        _root_cause_selector_collection_plan_metrics(
            ROOT_CAUSE_SELECTOR_COLLECTION_PLAN_SUMMARY,
            ROOT_CAUSE_SELECTOR_COLLECTION_PLAN_REPORT,
        )
    )
    checks["root_cause_selector_collection_schema_coverage"] = (
        _root_cause_selector_collection_schema_coverage_metrics(
            ROOT_CAUSE_SELECTOR_COLLECTION_SCHEMA_COVERAGE_SUMMARY,
            ROOT_CAUSE_SELECTOR_COLLECTION_SCHEMA_COVERAGE_REPORT,
        )
    )
    checks["root_cause_selector_holdout_collection_manifest"] = (
        _root_cause_selector_holdout_collection_manifest_metrics(
            ROOT_CAUSE_SELECTOR_HOLDOUT_COLLECTION_MANIFEST_SUMMARY,
            ROOT_CAUSE_SELECTOR_HOLDOUT_COLLECTION_MANIFEST_REPORT,
        )
    )
    checks["root_cause_selector_holdout_collection_runbook"] = (
        _root_cause_selector_holdout_collection_runbook_metrics(
            ROOT_CAUSE_SELECTOR_HOLDOUT_COLLECTION_RUNBOOK_SUMMARY,
            ROOT_CAUSE_SELECTOR_HOLDOUT_COLLECTION_RUNBOOK_REPORT,
        )
    )
    checks["root_cause_selector_holdout_collection_capture_audit"] = (
        _root_cause_selector_holdout_collection_capture_audit_metrics(
            ROOT_CAUSE_SELECTOR_HOLDOUT_COLLECTION_CAPTURE_AUDIT_SUMMARY,
            ROOT_CAUSE_SELECTOR_HOLDOUT_COLLECTION_CAPTURE_AUDIT_REPORT,
        )
    )
    checks["root_cause_selector_holdout_priority_collection_capture_audit"] = (
        _root_cause_selector_holdout_priority_collection_capture_audit_metrics(
            ROOT_CAUSE_SELECTOR_HOLDOUT_PRIORITY_COLLECTION_CAPTURE_AUDIT_SUMMARY,
            ROOT_CAUSE_SELECTOR_HOLDOUT_PRIORITY_COLLECTION_CAPTURE_AUDIT_REPORT,
        )
    )
    checks["root_cause_selector_holdout_priority_capture_miss"] = (
        _root_cause_selector_holdout_priority_capture_miss_metrics(
            ROOT_CAUSE_SELECTOR_HOLDOUT_PRIORITY_CAPTURE_MISS_SUMMARY,
            ROOT_CAUSE_SELECTOR_HOLDOUT_PRIORITY_CAPTURE_MISS_REPORT,
        )
    )
    checks["root_cause_selector_holdout_blocker_status"] = (
        _root_cause_selector_holdout_blocker_status_metrics(
            ROOT_CAUSE_SELECTOR_HOLDOUT_BLOCKER_STATUS_SUMMARY,
            ROOT_CAUSE_SELECTOR_HOLDOUT_BLOCKER_STATUS_REPORT,
        )
    )
    checks["root_cause_worker_negative_column_roi_blocker"] = (
        _root_cause_worker_negative_column_roi_blocker_metrics(
            ROOT_CAUSE_WORKER_NEGATIVE_COLUMN_ROI_BLOCKER_SUMMARY,
            ROOT_CAUSE_WORKER_NEGATIVE_COLUMN_ROI_BLOCKER_REPORT,
        )
    )
    checks["root_cause_selector_context_trajectory_protocol"] = (
        _root_cause_selector_context_trajectory_protocol_metrics(
            ROOT_CAUSE_SELECTOR_CONTEXT_TRAJECTORY_PROTOCOL_SUMMARY,
            ROOT_CAUSE_SELECTOR_CONTEXT_TRAJECTORY_PROTOCOL_REPORT,
        )
    )
    checks["root_cause_selector_holdout_context_worklist"] = (
        _root_cause_selector_holdout_context_worklist_metrics(
            ROOT_CAUSE_SELECTOR_HOLDOUT_CONTEXT_WORKLIST_SUMMARY,
            ROOT_CAUSE_SELECTOR_HOLDOUT_CONTEXT_WORKLIST_REPORT,
        )
    )
    checks["root_cause_selector_holdout_context_action_plan"] = (
        _root_cause_selector_holdout_context_action_plan_metrics(
            ROOT_CAUSE_SELECTOR_HOLDOUT_CONTEXT_ACTION_PLAN_SUMMARY,
            ROOT_CAUSE_SELECTOR_HOLDOUT_CONTEXT_ACTION_PLAN_REPORT,
        )
    )
    checks["root_cause_selector_holdout_target002_drift_audit"] = (
        _root_cause_selector_holdout_target002_drift_audit_metrics(
            ROOT_CAUSE_SELECTOR_HOLDOUT_TARGET002_DRIFT_AUDIT_SUMMARY,
            ROOT_CAUSE_SELECTOR_HOLDOUT_TARGET002_DRIFT_AUDIT_REPORT,
        )
    )
    checks["root_cause_selector_holdout_target002_probe_matrix"] = (
        _root_cause_selector_holdout_target002_probe_matrix_metrics(
            ROOT_CAUSE_SELECTOR_HOLDOUT_TARGET002_PROBE_MATRIX_SUMMARY,
            ROOT_CAUSE_SELECTOR_HOLDOUT_TARGET002_PROBE_MATRIX_REPORT,
        )
    )
    checks["root_cause_selector_holdout_target002_trajectory_branch"] = (
        _root_cause_selector_holdout_target002_trajectory_branch_metrics(
            ROOT_CAUSE_SELECTOR_HOLDOUT_TARGET002_TRAJECTORY_BRANCH_SUMMARY,
            ROOT_CAUSE_SELECTOR_HOLDOUT_TARGET002_TRAJECTORY_BRANCH_REPORT,
        )
    )
    checks["root_cause_selector_holdout_missing_context_diagnosis"] = (
        _root_cause_selector_holdout_missing_context_diagnosis_metrics(
            ROOT_CAUSE_SELECTOR_HOLDOUT_MISSING_CONTEXT_DIAGNOSIS_SUMMARY,
            ROOT_CAUSE_SELECTOR_HOLDOUT_MISSING_CONTEXT_DIAGNOSIS_REPORT,
        )
    )
    checks["root_cause_selector_holdout_target002_component_drift"] = (
        _root_cause_selector_holdout_target002_component_drift_metrics(
            ROOT_CAUSE_SELECTOR_HOLDOUT_TARGET002_COMPONENT_DRIFT_SUMMARY,
            ROOT_CAUSE_SELECTOR_HOLDOUT_TARGET002_COMPONENT_DRIFT_REPORT,
        )
    )
    checks["root_cause_selector_component_feature_readiness"] = (
        _root_cause_selector_component_feature_readiness_metrics(
            ROOT_CAUSE_SELECTOR_COMPONENT_FEATURE_READINESS_SUMMARY,
            ROOT_CAUSE_SELECTOR_COMPONENT_FEATURE_READINESS_REPORT,
        )
    )
    checks["root_cause_selector_component_capture_schema_contract"] = (
        _root_cause_selector_component_capture_schema_contract_metrics(
            ROOT_CAUSE_SELECTOR_COMPONENT_CAPTURE_SCHEMA_CONTRACT_SUMMARY,
            ROOT_CAUSE_SELECTOR_COMPONENT_CAPTURE_SCHEMA_CONTRACT_REPORT,
        )
    )
    checks["root_cause_component_payload_addition_before_rows"] = (
        _root_cause_component_payload_addition_before_rows_metrics(
            ROOT_CAUSE_COMPONENT_PAYLOAD_ADDITION_BEFORE_ROWS_SUMMARY,
            ROOT_CAUSE_COMPONENT_PAYLOAD_ADDITION_BEFORE_ROWS_REPORT,
        )
    )
    checks["root_cause_component_payload_selector_holdout_extension"] = (
        _root_cause_component_payload_selector_holdout_extension_metrics(
            ROOT_CAUSE_COMPONENT_PAYLOAD_SELECTOR_HOLDOUT_EXTENSION_SUMMARY,
            ROOT_CAUSE_COMPONENT_PAYLOAD_SELECTOR_HOLDOUT_EXTENSION_REPORT,
        )
    )
    checks["root_cause_selector_context_sufficiency_gap"] = (
        _root_cause_selector_context_sufficiency_gap_metrics(
            ROOT_CAUSE_SELECTOR_CONTEXT_SUFFICIENCY_GAP_SUMMARY,
            ROOT_CAUSE_SELECTOR_CONTEXT_SUFFICIENCY_GAP_REPORT,
        )
    )
    checks["root_cause_selector_pool_overlap_feature_probe"] = (
        _root_cause_selector_pool_overlap_feature_probe_metrics(
            ROOT_CAUSE_SELECTOR_POOL_OVERLAP_FEATURE_PROBE_SUMMARY,
            ROOT_CAUSE_SELECTOR_POOL_OVERLAP_FEATURE_PROBE_REPORT,
        )
    )
    checks["root_cause_selector_context_schema_gap"] = (
        _root_cause_selector_context_schema_gap_metrics(
            ROOT_CAUSE_SELECTOR_CONTEXT_SCHEMA_GAP_SUMMARY,
            ROOT_CAUSE_SELECTOR_CONTEXT_SCHEMA_GAP_REPORT,
        )
    )
    checks["root_cause_selector_snapshot_sample_coverage"] = (
        _root_cause_selector_snapshot_sample_coverage_metrics(
            ROOT_CAUSE_SELECTOR_SNAPSHOT_SAMPLE_COVERAGE_SUMMARY,
            ROOT_CAUSE_SELECTOR_SNAPSHOT_SAMPLE_COVERAGE_REPORT,
        )
    )
    checks["root_cause_selector_next_feature_gate"] = (
        _root_cause_selector_next_feature_gate_metrics(
            ROOT_CAUSE_SELECTOR_NEXT_FEATURE_GATE_SUMMARY,
            ROOT_CAUSE_SELECTOR_NEXT_FEATURE_GATE_REPORT,
        )
    )
    checks["goal_current_summary"] = _goal_current_summary_metrics(GOAL_SUMMARY)
    checks["exact_context_capture_status"] = _exact_context_capture_status_metrics(
        EXACT_CONTEXT_CAPTURE_STATUS_SUMMARY,
        EXACT_CONTEXT_CAPTURE_STATUS_REPORT,
    )
    checks["selector_holdout_status"] = _selector_holdout_status_metrics(
        SELECTOR_HOLDOUT_STATUS_SUMMARY,
        SELECTOR_HOLDOUT_STATUS_REPORT,
    )
    checks["selector_error_anatomy"] = _selector_error_anatomy_metrics(
        SELECTOR_ERROR_ANATOMY_SUMMARY,
        SELECTOR_ERROR_ANATOMY_REPORT,
    )
    checks["selector_counterexample_catalog"] = (
        _selector_counterexample_catalog_metrics(
            SELECTOR_COUNTEREXAMPLE_CATALOG_SUMMARY,
            SELECTOR_COUNTEREXAMPLE_CATALOG_REPORT,
        )
    )
    checks["production_selector_blocker_catalog"] = (
        _production_selector_blocker_catalog_metrics(
            PRODUCTION_SELECTOR_BLOCKER_CATALOG_SUMMARY,
            PRODUCTION_SELECTOR_BLOCKER_CATALOG_REPORT,
        )
    )
    checks["selector_failure_mechanism_audit"] = (
        _selector_failure_mechanism_audit_metrics(
            SELECTOR_FAILURE_MECHANISM_AUDIT_SUMMARY,
            SELECTOR_FAILURE_MECHANISM_AUDIT_REPORT,
        )
    )
    checks["selector_context_feature_gap_audit"] = (
        _selector_context_feature_gap_audit_metrics(
            SELECTOR_CONTEXT_FEATURE_GAP_AUDIT_SUMMARY,
            SELECTOR_CONTEXT_FEATURE_GAP_AUDIT_REPORT,
        )
    )
    checks["selector_feature_availability_audit"] = (
        _selector_feature_availability_audit_metrics(
            SELECTOR_FEATURE_AVAILABILITY_AUDIT_SUMMARY,
            SELECTOR_FEATURE_AVAILABILITY_AUDIT_REPORT,
        )
    )
    checks["capture_schema_feasibility_audit"] = (
        _capture_schema_feasibility_audit_metrics(
            CAPTURE_SCHEMA_FEASIBILITY_AUDIT_SUMMARY,
            CAPTURE_SCHEMA_FEASIBILITY_AUDIT_REPORT,
        )
    )
    checks["remaining_rmp_trajectory_field_recovery"] = (
        _remaining_rmp_trajectory_field_recovery_metrics(
            REMAINING_RMP_TRAJECTORY_FIELD_RECOVERY_SUMMARY,
            REMAINING_RMP_TRAJECTORY_FIELD_RECOVERY_REPORT,
        )
    )
    checks["active_basis_observability_gap"] = (
        _active_basis_observability_gap_metrics(
            ACTIVE_BASIS_OBSERVABILITY_GAP_SUMMARY,
            ACTIVE_BASIS_OBSERVABILITY_GAP_REPORT,
        )
    )
    checks["active_basis_capture_schema_feasibility"] = (
        _active_basis_capture_schema_feasibility_metrics(
            ACTIVE_BASIS_CAPTURE_SCHEMA_FEASIBILITY_SUMMARY,
            ACTIVE_BASIS_CAPTURE_SCHEMA_FEASIBILITY_REPORT,
        )
    )
    checks["active_basis_snapshot_smoke"] = _active_basis_snapshot_smoke_metrics(
        ACTIVE_BASIS_SNAPSHOT_SMOKE_SUMMARY,
        ACTIVE_BASIS_SNAPSHOT_SMOKE_REPORT,
    )
    checks["active_basis_snapshot_mt20_smoke"] = (
        _active_basis_snapshot_mt20_smoke_metrics(
            ACTIVE_BASIS_SNAPSHOT_MT20_SMOKE_SUMMARY,
            ACTIVE_BASIS_SNAPSHOT_MT20_SMOKE_REPORT,
        )
    )
    checks["active_basis_snapshot_multi20_smoke"] = (
        _active_basis_snapshot_multi20_smoke_metrics(
            ACTIVE_BASIS_SNAPSHOT_MULTI20_SMOKE_SUMMARY,
            ACTIVE_BASIS_SNAPSHOT_MULTI20_SMOKE_REPORT,
        )
    )
    checks["active_basis_snapshot_greedy_apollo20_02_smoke"] = (
        _active_basis_snapshot_greedy_apollo20_02_smoke_metrics(
            ACTIVE_BASIS_SNAPSHOT_GREEDY_APOLLO20_02_SMOKE_SUMMARY,
            ACTIVE_BASIS_SNAPSHOT_GREEDY_APOLLO20_02_SMOKE_REPORT,
        )
    )
    checks["active_basis_snapshot_greedy20_pair_smoke"] = (
        _active_basis_snapshot_greedy20_pair_smoke_metrics(
            ACTIVE_BASIS_SNAPSHOT_GREEDY20_PAIR_SMOKE_SUMMARY,
            ACTIVE_BASIS_SNAPSHOT_GREEDY20_PAIR_SMOKE_REPORT,
        )
    )
    checks["active_basis_snapshot_selector_signal"] = (
        _active_basis_snapshot_selector_signal_metrics(
            ACTIVE_BASIS_SNAPSHOT_SELECTOR_SIGNAL_SUMMARY,
            ACTIVE_BASIS_SNAPSHOT_SELECTOR_SIGNAL_REPORT,
        )
    )
    checks["active_basis_snapshot_counterexamples"] = (
        _active_basis_snapshot_counterexamples_metrics(
            ACTIVE_BASIS_SNAPSHOT_COUNTEREXAMPLES_SUMMARY,
            ACTIVE_BASIS_SNAPSHOT_COUNTEREXAMPLES_REPORT,
        )
    )
    checks["selector_enriched_rmp_feature_holdout"] = (
        _selector_enriched_rmp_feature_holdout_metrics(
            SELECTOR_ENRICHED_RMP_FEATURE_HOLDOUT_SUMMARY,
            SELECTOR_ENRICHED_RMP_FEATURE_HOLDOUT_REPORT,
        )
    )
    checks["selector_enriched_multifeature_model_holdout"] = (
        _selector_enriched_multifeature_model_holdout_metrics(
            SELECTOR_ENRICHED_MULTIFEATURE_MODEL_HOLDOUT_SUMMARY,
            SELECTOR_ENRICHED_MULTIFEATURE_MODEL_HOLDOUT_REPORT,
        )
    )
    checks["production_ab_entry_gate_catalog"] = (
        _production_ab_entry_gate_catalog_metrics(
            PRODUCTION_AB_ENTRY_GATE_CATALOG_SUMMARY,
            PRODUCTION_AB_ENTRY_GATE_CATALOG_REPORT,
        )
    )
    checks["optimization_direction_candidate_registry"] = (
        _optimization_direction_candidate_registry_metrics(
            OPTIMIZATION_DIRECTION_CANDIDATE_REGISTRY_SUMMARY,
            OPTIMIZATION_DIRECTION_CANDIDATE_REGISTRY_REPORT,
        )
    )
    checks["selector_threshold_frontier"] = _selector_threshold_frontier_metrics(
        SELECTOR_THRESHOLD_FRONTIER_SUMMARY,
        SELECTOR_THRESHOLD_FRONTIER_REPORT,
    )
    checks["selector_context_collision"] = _selector_context_collision_metrics(
        SELECTOR_CONTEXT_COLLISION_SUMMARY,
        SELECTOR_CONTEXT_COLLISION_REPORT,
    )
    checks["selector_local_feature_direction"] = (
        _selector_local_feature_direction_metrics(
            SELECTOR_LOCAL_FEATURE_DIRECTION_SUMMARY,
            SELECTOR_LOCAL_FEATURE_DIRECTION_REPORT,
        )
    )
    checks["selector_context_disambiguation"] = (
        _selector_context_disambiguation_metrics(
            SELECTOR_CONTEXT_DISAMBIGUATION_SUMMARY,
            SELECTOR_CONTEXT_DISAMBIGUATION_REPORT,
        )
    )
    checks["selector_context_scalar_candidates"] = (
        _selector_context_scalar_candidates_metrics(
            SELECTOR_CONTEXT_SCALAR_CANDIDATES_SUMMARY,
            SELECTOR_CONTEXT_SCALAR_CANDIDATES_REPORT,
        )
    )
    checks["selector_context_scalar_holdout"] = (
        _selector_context_scalar_holdout_metrics(
            SELECTOR_CONTEXT_SCALAR_HOLDOUT_SUMMARY,
            SELECTOR_CONTEXT_SCALAR_HOLDOUT_REPORT,
        )
    )
    checks["selector_micro_vs_fold_gate"] = (
        _selector_micro_vs_fold_gate_metrics(
            SELECTOR_MICRO_VS_FOLD_GATE_SUMMARY,
            SELECTOR_MICRO_VS_FOLD_GATE_REPORT,
        )
    )
    checks["selector_model_micro_vs_fold_gate"] = (
        _selector_model_micro_vs_fold_gate_metrics(
            SELECTOR_MODEL_MICRO_VS_FOLD_GATE_SUMMARY,
            SELECTOR_MODEL_MICRO_VS_FOLD_GATE_REPORT,
        )
    )
    checks["selector_rule_family_search"] = (
        _selector_rule_family_search_metrics(
            SELECTOR_RULE_FAMILY_SEARCH_SUMMARY,
            SELECTOR_RULE_FAMILY_SEARCH_REPORT,
        )
    )
    checks["selector_rule_family_search_20only"] = (
        _selector_rule_family_search_metrics(
            SELECTOR_RULE_FAMILY_SEARCH_20ONLY_SUMMARY,
            SELECTOR_RULE_FAMILY_SEARCH_20ONLY_REPORT,
            expected_row_count=279,
            expected_rule_count_min=18000,
            expected_task_count_filter=20,
        )
    )
    checks["selector_rule_family_train_holdout"] = (
        _selector_rule_family_train_holdout_metrics(
            SELECTOR_RULE_FAMILY_TRAIN_HOLDOUT_SUMMARY,
            SELECTOR_RULE_FAMILY_TRAIN_HOLDOUT_REPORT,
        )
    )
    checks["selector_rule_family_train_holdout_20only"] = (
        _selector_rule_family_train_holdout_metrics(
            SELECTOR_RULE_FAMILY_TRAIN_HOLDOUT_20ONLY_SUMMARY,
            SELECTOR_RULE_FAMILY_TRAIN_HOLDOUT_20ONLY_REPORT,
            expected_row_count=279,
            expected_task_count_filter=20,
        )
    )
    checks["selector_context_fold_anatomy"] = (
        _selector_context_fold_anatomy_metrics(
            SELECTOR_CONTEXT_FOLD_ANATOMY_SUMMARY,
            SELECTOR_CONTEXT_FOLD_ANATOMY_REPORT,
        )
    )
    checks["selector_context_feature_anatomy"] = (
        _selector_context_feature_anatomy_metrics(
            SELECTOR_CONTEXT_FEATURE_ANATOMY_SUMMARY,
            SELECTOR_CONTEXT_FEATURE_ANATOMY_REPORT,
        )
    )
    checks["root_cause_code_boundary"] = _root_cause_code_boundary_metrics(
        ROOT_CAUSE_CODE_BOUNDARY_SUMMARY,
        ROOT_CAUSE_CODE_BOUNDARY_REPORT,
    )
    checks["root_cause_failure_matrix"] = _root_cause_failure_matrix_metrics(
        ROOT_CAUSE_FAILURE_MATRIX_SUMMARY,
        ROOT_CAUSE_FAILURE_MATRIX_REPORT,
    )
    checks["optimization_direction_readiness"] = _optimization_direction_readiness_metrics(
        checks
    )
    checks["goal_completion_audit"] = _goal_completion_audit_metrics(checks)
    all_checks_pass = (
        checks["small_scale_overhead"]["check_triggered_all_worse"]
        and checks["small_scale_overhead"]["check_nontriggered_no_official_change"]
        and checks["current_small_summary_scan"]["check_current_scan_same_direction"]
        and checks["phase7o_worker_roi"]["check_worker_no_stable_roi"]
        and checks["phase8q_worker_add_columns"]["check_worker_can_add_but_not_solve"]
        and checks["candidate_batch_selector"]["check_candidate_batch_selector_not_stable"]
        and checks["candidate_selector_models"]["check_no_simple_model_passes_strict_gate"]
        and checks["selector_failure_anatomy"][
            "check_selector_failure_anatomy_supports_root_cause"
        ]
        and checks["hindsight_oracle_gap"][
            "check_hindsight_oracle_gap_supports_root_cause"
        ]
        and checks["candidate_label_granularity"][
            "check_candidate_labels_are_batch_level_not_causal"
        ]
        and checks["batch_level_selector"]["check_batch_level_selector_still_not_stable"]
        and checks["trajectory_signal_ladder"]["check_signal_ladder_supports_root_cause"]
        and checks["batch_gate_stability"]["check_batch_gates_are_not_stable"]
        and checks["context_stratification"][
            "check_context_stratification_explains_gate_failure"
        ]
        and checks["context_only_baseline"]["check_context_only_has_signal_but_not_enough"]
        and checks["matched_context_audit"]["check_matched_context_needs_counterfactual"]
        and checks["matched_context_pairwise"]["check_pairwise_contrast_requires_replay"]
        and checks["exact_context_label_conflicts"][
            "check_observational_labels_not_causal_for_batch"
        ]
        and checks["counterfactual_replay_coverage"][
            "check_existing_replay_is_candidate_only"
        ]
        and checks["counterfactual_replay_candidates"][
            "check_replay_candidate_manifest_ready"
        ]
        and checks["counterfactual_replay_readiness"][
            "check_replay_manifest_not_exact_replay_ready"
        ]
        and checks["counterfactual_replay_materialization"][
            "check_observed_entries_materialize_but_replay_still_partial"
        ]
        and checks["counterfactual_replay_capture_smoke"][
            "check_capture_smoke_replay_payload_ready"
        ]
        and checks["counterfactual_replay_manifest_smoke"][
            "check_replay_manifest_smoke_ready_but_not_optimization_evidence"
        ]
        and checks["counterfactual_replay_feasible_smoke"][
            "check_duplicate_negative_replay_is_noop"
        ]
        and checks["counterfactual_replay_gap"][
            "check_real_additions_still_need_capture_for_replay"
        ]
        and checks["counterfactual_replay_real_capture"][
            "check_real_capture_replay_has_local_rmp_impact"
        ]
        and checks["counterfactual_replay_impact_dataset"][
            "check_impact_dataset_separates_high_impact_and_noop"
        ]
        and checks["counterfactual_replay_payload_quality"][
            "check_payload_quality_guard_rejects_unsolved_control"
        ]
        and checks["counterfactual_replay_capture_expansion"][
            "check_capture_expansion_confirms_unstable_capture"
        ]
        and checks["counterfactual_replay_global_capture_scan"][
            "check_global_capture_scan_confirms_clean_replay_sample_scarce"
        ]
        and checks["counterfactual_replay_candidate_to_capture_gap"][
            "check_replay_candidate_targets_initially_needed_exact_capture"
        ]
        and checks["counterfactual_capture_targets"][
            "check_capture_targets_are_precise_no_certificate_targets"
        ]
        and checks["counterfactual_capture_target_coverage"][
            "check_capture_targets_have_partial_exact_capture_coverage"
        ]
        and checks["counterfactual_target_tranq20_replay"][
            "check_tranq20_target_replay_has_local_rmp_impact"
        ]
        and checks["counterfactual_target_001_002_replay"][
            "check_target_001_002_replay_has_local_rmp_impact"
        ]
        and checks["counterfactual_target002_reproduction_gap"][
            "check_target002_gap_is_cg1_trajectory_drift"
        ]
        and checks["counterfactual_replay_selector_gate"][
            "check_exact_replay_selector_gate_rejects_simple_rules"
        ]
        and checks["counterfactual_replay_pair_selector_gate"][
            "check_exact_replay_pair_selector_gate_rejects_simple_pairs"
        ]
        and checks["counterfactual_replay_model_selector_gate"][
            "check_exact_replay_model_selector_gate_rejects_simple_models"
        ]
        and checks["counterfactual_target002_pt03_recovery"][
            "check_target002_pt03_recovery_and_exact_replay"
        ]
        and checks["counterfactual_replay_selector_gate_with_target002_pt03"][
            "check_selector_gate_shift_has_calibrated_candidates"
        ]
        and checks["replay_calibrated_selector_candidate"][
            "check_replay_calibrated_selector_candidate_is_ab_only"
        ]
        and checks["calibrated_selector_ab_profile_smoke"][
            "check_calibrated_selector_profile_smoke_is_wiring_only"
        ]
        and checks["counterfactual_replay_dataset_structure"][
            "check_exact_replay_dataset_structure_requires_calibration_only"
        ]
        and checks["counterfactual_capture_priority"][
            "check_counterfactual_capture_priority_is_calibration_only"
        ]
        and checks["optimization_direction_readiness"][
            "check_root_cause_known_but_optimization_direction_unproven"
        ]
        and checks["final_report"]["exists"]
        and checks["requirement_audit_report"][
            "check_requirement_audit_report_is_current"
        ]
        and checks["optimization_direction_readiness_report"][
            "check_optimization_direction_readiness_report_is_current"
        ]
        and checks["root_cause_diagnosis_report"][
            "check_root_cause_diagnosis_report_is_current"
        ]
        and checks["goal_completion_blockers_report"][
            "check_goal_completion_blockers_report_is_current"
        ]
        and checks["objective_completion_audit_catalog"][
            "check_objective_completion_audit_catalog_is_current"
        ]
        and checks["next_evidence_protocol_catalog"][
            "check_next_evidence_protocol_catalog_is_current"
        ]
        and checks["evidence_bundle_manifest"][
            "check_evidence_bundle_manifest_is_current"
        ]
        and checks["root_cause_current_answer"][
            "check_root_cause_current_answer_is_current"
        ]
        and checks["root_cause_causal_chain_audit"][
            "check_root_cause_causal_chain_audit_is_current"
        ]
        and checks["root_cause_stale_claims"][
            "check_root_cause_stale_claims_is_current"
        ]
        and checks["root_cause_missing_requirement_evidence_scan"][
            "check_missing_requirement_evidence_scan_is_current"
        ]
        and checks["root_cause_next_action_plan"][
            "check_root_cause_next_action_plan_is_current"
        ]
        and checks["root_cause_document_consistency"][
            "check_root_cause_document_consistency_is_current"
        ]
        and checks["root_cause_selector_collection_plan"][
            "check_root_cause_selector_collection_plan_is_current"
        ]
        and checks["root_cause_selector_collection_schema_coverage"][
            "check_root_cause_selector_collection_schema_coverage_is_current"
        ]
        and checks["root_cause_selector_holdout_collection_manifest"][
            "check_root_cause_selector_holdout_collection_manifest_is_current"
        ]
        and checks["root_cause_selector_holdout_collection_runbook"][
            "check_root_cause_selector_holdout_collection_runbook_is_current"
        ]
        and checks["root_cause_selector_holdout_collection_capture_audit"][
            "check_root_cause_selector_holdout_collection_capture_audit_is_current"
        ]
        and checks["root_cause_selector_holdout_priority_collection_capture_audit"][
            "check_root_cause_selector_holdout_priority_collection_capture_audit_is_current"
        ]
        and checks["root_cause_selector_holdout_priority_capture_miss"][
            "check_root_cause_selector_holdout_priority_capture_miss_is_current"
        ]
        and checks["root_cause_selector_holdout_blocker_status"][
            "check_root_cause_selector_holdout_blocker_status_is_current"
        ]
        and checks["root_cause_worker_negative_column_roi_blocker"][
            "check_root_cause_worker_negative_column_roi_blocker_is_current"
        ]
        and checks["root_cause_selector_context_trajectory_protocol"][
            "check_root_cause_selector_context_trajectory_protocol_is_current"
        ]
        and checks["root_cause_selector_holdout_context_worklist"][
            "check_root_cause_selector_holdout_context_worklist_is_current"
        ]
        and checks["root_cause_selector_holdout_context_action_plan"][
            "check_root_cause_selector_holdout_context_action_plan_is_current"
        ]
        and checks["root_cause_selector_holdout_target002_drift_audit"][
            "check_root_cause_selector_holdout_target002_drift_audit_is_current"
        ]
        and checks["root_cause_selector_holdout_target002_probe_matrix"][
            "check_root_cause_selector_holdout_target002_probe_matrix_is_current"
        ]
        and checks["root_cause_selector_holdout_target002_trajectory_branch"][
            "check_root_cause_selector_holdout_target002_trajectory_branch_is_current"
        ]
        and checks["root_cause_selector_holdout_missing_context_diagnosis"][
            "check_root_cause_selector_holdout_missing_context_diagnosis_is_current"
        ]
        and checks["root_cause_selector_holdout_target002_component_drift"][
            "check_root_cause_selector_holdout_target002_component_drift_is_current"
        ]
        and checks["root_cause_selector_component_feature_readiness"][
            "check_root_cause_selector_component_feature_readiness_is_current"
        ]
        and checks["root_cause_selector_component_capture_schema_contract"][
            "check_root_cause_selector_component_capture_schema_contract_is_current"
        ]
        and checks["root_cause_component_payload_addition_before_rows"][
            "check_component_payload_addition_before_rows_is_current"
        ]
        and checks["root_cause_component_payload_selector_holdout_extension"][
            "check_component_payload_selector_holdout_extension_is_current"
        ]
        and checks["root_cause_selector_context_sufficiency_gap"][
            "check_root_cause_selector_context_sufficiency_gap_is_current"
        ]
        and checks["root_cause_selector_pool_overlap_feature_probe"][
            "check_selector_pool_overlap_feature_probe_is_current"
        ]
        and checks["root_cause_selector_context_schema_gap"][
            "check_selector_context_schema_gap_is_current"
        ]
        and checks["root_cause_selector_snapshot_sample_coverage"][
            "check_selector_snapshot_sample_coverage_is_current"
        ]
        and checks["root_cause_selector_next_feature_gate"][
            "check_root_cause_selector_next_feature_gate_is_current"
        ]
        # The rebuild report is generated by a wrapper that itself runs this
        # verifier.  Keep its status observable in the ledger, but do not make
        # verifier validity depend on a self-referential artifact.
        and checks["goal_current_summary"]["check_goal_current_summary_is_current"]
        and checks["exact_context_capture_status"][
            "check_exact_context_capture_ready_for_calibration_only"
        ]
        and checks["selector_holdout_status"][
            "check_selector_holdout_not_production_validated"
        ]
        and checks["selector_error_anatomy"][
            "check_selector_error_anatomy_blocks_simple_selector"
        ]
        and checks["selector_counterexample_catalog"][
            "check_selector_counterexamples_block_production_selector"
        ]
        and checks["production_selector_blocker_catalog"][
            "check_production_selector_blockers_are_current"
        ]
        and checks["selector_failure_mechanism_audit"][
            "check_selector_failure_mechanism_audit_is_current"
        ]
        and checks["selector_context_feature_gap_audit"][
            "check_selector_context_feature_gap_audit_is_current"
        ]
        and checks["selector_feature_availability_audit"][
            "check_selector_feature_availability_audit_is_current"
        ]
        and checks["capture_schema_feasibility_audit"][
            "check_capture_schema_feasibility_audit_is_current"
        ]
        and checks["remaining_rmp_trajectory_field_recovery"][
            "check_remaining_rmp_trajectory_field_recovery_is_current"
        ]
        and checks["active_basis_observability_gap"][
            "check_active_basis_observability_gap_is_current"
        ]
        and checks["active_basis_capture_schema_feasibility"][
            "check_active_basis_capture_schema_feasibility_is_current"
        ]
        and checks["active_basis_snapshot_smoke"][
            "check_active_basis_snapshot_smoke_is_current"
        ]
        and checks["active_basis_snapshot_mt20_smoke"][
            "check_active_basis_snapshot_mt20_smoke_is_current"
        ]
        and checks["active_basis_snapshot_multi20_smoke"][
            "check_active_basis_snapshot_multi20_smoke_is_current"
        ]
        and checks["active_basis_snapshot_greedy_apollo20_02_smoke"][
            "check_active_basis_snapshot_greedy_apollo20_02_smoke_is_current"
        ]
        and checks["active_basis_snapshot_greedy20_pair_smoke"][
            "check_active_basis_snapshot_greedy20_pair_smoke_is_current"
        ]
        and checks["active_basis_snapshot_selector_signal"][
            "check_active_basis_snapshot_selector_signal_is_current"
        ]
        and checks["active_basis_snapshot_counterexamples"][
            "check_active_basis_snapshot_counterexamples_is_current"
        ]
        and checks["selector_enriched_rmp_feature_holdout"][
            "check_selector_enriched_rmp_feature_holdout_is_current"
        ]
        and checks["selector_enriched_multifeature_model_holdout"][
            "check_selector_enriched_multifeature_model_holdout_is_current"
        ]
        and checks["production_ab_entry_gate_catalog"][
            "check_production_ab_entry_gate_is_blocked"
        ]
        and checks["optimization_direction_candidate_registry"][
            "check_optimization_direction_registry_is_current"
        ]
        and checks["selector_threshold_frontier"][
            "check_threshold_frontier_rules_out_simple_threshold"
        ]
        and checks["selector_context_collision"][
            "check_selector_context_collision_blocks_column_local_selector"
        ]
        and checks["selector_local_feature_direction"][
            "check_selector_local_feature_direction_blocks_monotone_selector"
        ]
        and checks["selector_context_disambiguation"][
            "check_context_disambiguation_supports_context_coupling"
        ]
        and checks["selector_context_scalar_candidates"][
            "check_context_scalar_candidate_is_calibration_only"
        ]
        and checks["selector_context_scalar_holdout"][
            "check_context_scalar_holdout_rejects_simple_rules"
        ]
        and checks["selector_micro_vs_fold_gate"][
            "check_micro_average_gate_is_not_production_selector"
        ]
        and checks["selector_model_micro_vs_fold_gate"][
            "check_model_aggregate_gate_is_not_production_selector"
        ]
        and checks["selector_rule_family_search"][
            "check_rule_family_search_rejects_simple_conjunctions"
        ]
        and checks["selector_rule_family_search_20only"][
            "check_rule_family_search_rejects_simple_conjunctions"
        ]
        and checks["selector_rule_family_train_holdout"][
            "check_train_holdout_rule_family_not_context_stable"
        ]
        and checks["selector_rule_family_train_holdout_20only"][
            "check_train_holdout_rule_family_not_context_stable"
        ]
        and checks["selector_context_fold_anatomy"][
            "check_context_fold_anatomy_supports_context_trajectory_root_cause"
        ]
        and checks["selector_context_feature_anatomy"][
            "check_context_feature_anatomy_supports_context_root_cause"
        ]
        and checks["root_cause_code_boundary"][
            "check_code_boundary_no_unvalidated_production_effect"
        ]
        and checks["root_cause_failure_matrix"][
            "check_failure_matrix_routes_have_evidence"
        ]
        and checks["goal_completion_audit"][
            "check_goal_completion_audit_is_consistent"
        ]
    )
    readiness = checks["optimization_direction_readiness"]
    goal_audit = checks["goal_completion_audit"]
    completion_requirements = readiness["completion_requirements"]
    missing_requirements = readiness["missing_requirements"]
    next_evidence_gates = readiness["next_evidence_gates"]
    objective_requirement_audit = {
        "schema_version": "objective_requirement_audit_v1",
        "audit_items": goal_audit["audit_items"],
        "blocking_missing_requirements": goal_audit[
            "blocking_missing_requirements"
        ],
        "root_cause_explanation_supported": True,
        "not_limited_to_pulse": any(
            item.get("requirement") == "not_limited_to_pulse"
            and item.get("status") == "proved"
            for item in goal_audit["audit_items"]
        ),
        "stable_production_optimization_direction": bool(
            completion_requirements["production_direction_proven"]
        ),
        "exact_5_10_no_regression_and_20_speedup": bool(
            completion_requirements["has_small_no_regression_guard"]
            and completion_requirements["has_task5_noop_no_regression_guard"]
            and completion_requirements["has_task10_noop_no_regression_guard"]
            and completion_requirements["has_full_5_10_production_ab_evidence"]
            and completion_requirements["has_20_walltime_speedup_evidence"]
            and completion_requirements["production_direction_proven"]
        ),
        "decision": (
            "keep_goal_active"
            if not goal_audit["goal_complete"]
            else "mark_goal_complete"
        ),
    }
    replay_impact = checks["counterfactual_replay_impact_dataset"]
    replay_real_capture = replay_impact["real_capture"]
    replay_duplicate_noop = replay_impact["duplicate_noop"]
    selector_holdout = checks["selector_holdout_status"]
    selector_error_anatomy = checks["selector_error_anatomy"]
    selector_counterexample_catalog = checks["selector_counterexample_catalog"]
    production_selector_blocker_catalog = checks[
        "production_selector_blocker_catalog"
    ]
    selector_failure_mechanism_audit = checks[
        "selector_failure_mechanism_audit"
    ]
    selector_context_feature_gap_audit = checks[
        "selector_context_feature_gap_audit"
    ]
    selector_feature_availability_audit = checks[
        "selector_feature_availability_audit"
    ]
    capture_schema_feasibility_audit = checks[
        "capture_schema_feasibility_audit"
    ]
    remaining_rmp_trajectory_field_recovery = checks[
        "remaining_rmp_trajectory_field_recovery"
    ]
    active_basis_observability_gap = checks["active_basis_observability_gap"]
    active_basis_capture_schema_feasibility = checks[
        "active_basis_capture_schema_feasibility"
    ]
    active_basis_snapshot_smoke = checks["active_basis_snapshot_smoke"]
    active_basis_snapshot_mt20_smoke = checks[
        "active_basis_snapshot_mt20_smoke"
    ]
    active_basis_snapshot_multi20_smoke = checks[
        "active_basis_snapshot_multi20_smoke"
    ]
    active_basis_snapshot_greedy_apollo20_02_smoke = checks[
        "active_basis_snapshot_greedy_apollo20_02_smoke"
    ]
    active_basis_snapshot_greedy20_pair_smoke = checks[
        "active_basis_snapshot_greedy20_pair_smoke"
    ]
    active_basis_snapshot_selector_signal = checks[
        "active_basis_snapshot_selector_signal"
    ]
    active_basis_snapshot_counterexamples = checks[
        "active_basis_snapshot_counterexamples"
    ]
    selector_collection_schema_coverage = checks[
        "root_cause_selector_collection_schema_coverage"
    ]
    selector_holdout_collection_manifest = checks[
        "root_cause_selector_holdout_collection_manifest"
    ]
    selector_holdout_collection_runbook = checks[
        "root_cause_selector_holdout_collection_runbook"
    ]
    selector_holdout_collection_capture_audit = checks[
        "root_cause_selector_holdout_collection_capture_audit"
    ]
    selector_holdout_priority_collection_capture_audit = checks[
        "root_cause_selector_holdout_priority_collection_capture_audit"
    ]
    selector_holdout_priority_capture_miss = checks[
        "root_cause_selector_holdout_priority_capture_miss"
    ]
    selector_holdout_blocker_status = checks[
        "root_cause_selector_holdout_blocker_status"
    ]
    worker_negative_column_roi_blocker = checks[
        "root_cause_worker_negative_column_roi_blocker"
    ]
    selector_context_trajectory_protocol = checks[
        "root_cause_selector_context_trajectory_protocol"
    ]
    selector_holdout_context_worklist = checks[
        "root_cause_selector_holdout_context_worklist"
    ]
    selector_holdout_context_action_plan = checks[
        "root_cause_selector_holdout_context_action_plan"
    ]
    root_cause_causal_chain_audit = checks["root_cause_causal_chain_audit"]
    selector_holdout_target002_drift_audit = checks[
        "root_cause_selector_holdout_target002_drift_audit"
    ]
    selector_holdout_target002_probe_matrix = checks[
        "root_cause_selector_holdout_target002_probe_matrix"
    ]
    selector_holdout_target002_trajectory_branch = checks[
        "root_cause_selector_holdout_target002_trajectory_branch"
    ]
    selector_holdout_missing_context_diagnosis = checks[
        "root_cause_selector_holdout_missing_context_diagnosis"
    ]
    selector_holdout_target002_component_drift = checks[
        "root_cause_selector_holdout_target002_component_drift"
    ]
    selector_component_feature_readiness = checks[
        "root_cause_selector_component_feature_readiness"
    ]
    selector_component_capture_schema_contract = checks[
        "root_cause_selector_component_capture_schema_contract"
    ]
    component_payload_addition_before_rows = checks[
        "root_cause_component_payload_addition_before_rows"
    ]
    component_payload_selector_holdout_extension = checks[
        "root_cause_component_payload_selector_holdout_extension"
    ]
    selector_context_sufficiency_gap = checks[
        "root_cause_selector_context_sufficiency_gap"
    ]
    selector_pool_overlap_feature_probe = checks[
        "root_cause_selector_pool_overlap_feature_probe"
    ]
    selector_context_schema_gap = checks["root_cause_selector_context_schema_gap"]
    selector_snapshot_sample_coverage = checks[
        "root_cause_selector_snapshot_sample_coverage"
    ]
    selector_next_feature_gate = checks[
        "root_cause_selector_next_feature_gate"
    ]
    selector_enriched_rmp_feature_holdout = checks[
        "selector_enriched_rmp_feature_holdout"
    ]
    selector_enriched_multifeature_model_holdout = checks[
        "selector_enriched_multifeature_model_holdout"
    ]
    production_ab_entry_gate_catalog = checks[
        "production_ab_entry_gate_catalog"
    ]
    optimization_direction_candidate_registry = checks[
        "optimization_direction_candidate_registry"
    ]
    selector_threshold_frontier = checks["selector_threshold_frontier"]
    selector_context_collision = checks["selector_context_collision"]
    selector_local_feature_direction = checks["selector_local_feature_direction"]
    selector_context_disambiguation = checks["selector_context_disambiguation"]
    selector_context_scalar_candidates = checks["selector_context_scalar_candidates"]
    selector_context_scalar_holdout = checks["selector_context_scalar_holdout"]
    selector_micro_vs_fold_gate = checks["selector_micro_vs_fold_gate"]
    selector_model_micro_vs_fold_gate = checks[
        "selector_model_micro_vs_fold_gate"
    ]
    selector_rule_family_search = checks["selector_rule_family_search"]
    selector_rule_family_search_20only = checks[
        "selector_rule_family_search_20only"
    ]
    selector_rule_family_train_holdout = checks[
        "selector_rule_family_train_holdout"
    ]
    selector_rule_family_train_holdout_20only = checks[
        "selector_rule_family_train_holdout_20only"
    ]
    selector_context_fold_anatomy = checks["selector_context_fold_anatomy"]
    selector_context_feature_anatomy = checks["selector_context_feature_anatomy"]
    exact_capture_status = checks["exact_context_capture_status"]
    code_boundary = checks["root_cause_code_boundary"]
    failure_matrix = checks["root_cause_failure_matrix"]
    stale_claims = checks["root_cause_stale_claims"]
    missing_requirement_evidence_scan = checks[
        "root_cause_missing_requirement_evidence_scan"
    ]
    evidence_source_index = {
        "schema_version": "root_cause_evidence_source_index_v1",
        "entries": [
            {
                "conclusion_id": "small_scale_fixed_overhead_sensitivity",
                "status": "supported",
                "summary": (
                    "5/10 scale regression is explained by fixed overhead from "
                    "triggered worker/audit/probe mechanisms."
                ),
                "primary_artifacts": [
                    checks["small_scale_overhead"]["source"],
                ],
                "key_metrics": {
                    "triggered_rows": checks["small_scale_overhead"][
                        "triggered_rows"
                    ],
                    "triggered_worse_count": checks["small_scale_overhead"][
                        "triggered_worse_count"
                    ],
                    "triggered_better_count": checks["small_scale_overhead"][
                        "triggered_better_count"
                    ],
                    "nontriggered_official_changed": checks[
                        "small_scale_overhead"
                    ]["nontriggered_official_changed"],
                    "task5_nontriggered": checks["current_small_summary_scan"][
                        "task5_nontriggered"
                    ],
                    "task10_nontriggered": checks["current_small_summary_scan"][
                        "task10_nontriggered"
                    ],
                    "task10_triggered": checks["current_small_summary_scan"][
                        "task10_triggered"
                    ],
                },
            },
            {
                "conclusion_id": "twenty_negative_columns_not_sufficient",
                "status": "supported",
                "summary": (
                    "20-task runs can safely add true-RC negative journeys, but "
                    "that has not produced stable wall-time/status improvement."
                ),
                "primary_artifacts": [
                    checks["phase8q_worker_add_columns"]["source"],
                    worker_negative_column_roi_blocker["source"],
                    worker_negative_column_roi_blocker["report"],
                ],
                "key_metrics": {
                    "pulse_worker_returned_journeys": checks[
                        "phase8q_worker_add_columns"
                    ]["pulse_worker_returned_journeys"],
                    "pulse_worker_added_journeys": checks[
                        "phase8q_worker_add_columns"
                    ]["pulse_worker_added_journeys"],
                    "pulse_worker_added_new_task_set_count": checks[
                        "phase8q_worker_add_columns"
                    ]["pulse_worker_added_new_task_set_count"],
                    "all_time_limit": checks["phase8q_worker_add_columns"][
                        "all_time_limit"
                    ],
                    "completion_bound_retry_count": checks[
                        "phase8q_worker_add_columns"
                    ]["completion_bound_retry_count"],
                    "worker_negative_roi_blocker_status": (
                        worker_negative_column_roi_blocker["status"]
                    ),
                    "phase7o_worker_added_journeys": (
                        worker_negative_column_roi_blocker[
                            "phase7o_worker_added_journeys"
                        ]
                    ),
                    "phase7o_worker_added_new_task_sets": (
                        worker_negative_column_roi_blocker[
                            "phase7o_worker_added_new_task_sets"
                        ]
                    ),
                    "phase7o_nonbaseline_worsened_rows": (
                        worker_negative_column_roi_blocker[
                            "phase7o_nonbaseline_worsened_rows"
                        ]
                    ),
                    "phase7o_nonbaseline_rows": (
                        worker_negative_column_roi_blocker[
                            "phase7o_nonbaseline_rows"
                        ]
                    ),
                    "phase8q_worker_added_journeys": (
                        worker_negative_column_roi_blocker[
                            "phase8q_worker_added_journeys"
                        ]
                    ),
                    "phase8q_worker_added_rows": (
                        worker_negative_column_roi_blocker[
                            "phase8q_worker_added_rows"
                        ]
                    ),
                    "phase8q_improved_without_worker_added_count": (
                        worker_negative_column_roi_blocker[
                            "phase8q_improved_without_worker_added_count"
                        ]
                    ),
                },
            },
            {
                "conclusion_id": "true_rc_negative_can_be_high_impact_or_noop",
                "status": "supported",
                "summary": (
                    "Exact-context replay contains both high-impact returned "
                    "batches and no-op/replacement negative candidates."
                ),
                "primary_artifacts": list(replay_impact["sources"].values()),
                "key_metrics": {
                    "real_capture_high_impact_candidate_count": replay_real_capture[
                        "high_impact_candidate_count"
                    ],
                    "real_capture_best_objective_delta": replay_real_capture[
                        "best_objective_delta"
                    ],
                    "duplicate_noop_candidate_count": replay_duplicate_noop[
                        "noop_candidate_count"
                    ],
                    "duplicate_noop_best_objective_delta": replay_duplicate_noop[
                        "best_objective_delta"
                    ],
                },
            },
            {
                "conclusion_id": "selector_not_production_validated",
                "status": "blocking",
                "summary": (
                    "A replay-calibrated selector candidate exists, but it has "
                    "not passed the required context/instance/dataset holdout "
                    "and no production BPC A/B has validated it."
                ),
                "primary_artifacts": [
                    selector_holdout["source"],
                    selector_error_anatomy["source"],
                    selector_error_anatomy["report"],
                    selector_counterexample_catalog["source"],
                    selector_counterexample_catalog["report"],
                    production_selector_blocker_catalog["source"],
                    production_selector_blocker_catalog["report"],
                    selector_failure_mechanism_audit["source"],
                    selector_failure_mechanism_audit["report"],
                    selector_context_feature_gap_audit["source"],
                    selector_context_feature_gap_audit["report"],
                    selector_feature_availability_audit["source"],
                    selector_feature_availability_audit["report"],
                    capture_schema_feasibility_audit["source"],
                    capture_schema_feasibility_audit["report"],
                    remaining_rmp_trajectory_field_recovery["source"],
                    remaining_rmp_trajectory_field_recovery["report"],
                    active_basis_observability_gap["source"],
                    active_basis_observability_gap["report"],
                    active_basis_capture_schema_feasibility["source"],
                    active_basis_capture_schema_feasibility["report"],
                    active_basis_snapshot_smoke["source"],
                    active_basis_snapshot_smoke["report"],
                    active_basis_snapshot_mt20_smoke["source"],
                    active_basis_snapshot_mt20_smoke["report"],
                    active_basis_snapshot_multi20_smoke["source"],
                    active_basis_snapshot_multi20_smoke["report"],
                    active_basis_snapshot_greedy_apollo20_02_smoke["source"],
                    active_basis_snapshot_greedy_apollo20_02_smoke["report"],
                    active_basis_snapshot_greedy20_pair_smoke["source"],
                    active_basis_snapshot_greedy20_pair_smoke["report"],
                    active_basis_snapshot_selector_signal["source"],
                    active_basis_snapshot_selector_signal["report"],
                    active_basis_snapshot_counterexamples["source"],
                    active_basis_snapshot_counterexamples["report"],
                    selector_collection_schema_coverage["source"],
                    selector_collection_schema_coverage["report"],
                    selector_holdout_collection_manifest["source"],
                    selector_holdout_collection_manifest["report"],
                    selector_holdout_collection_runbook["source"],
                    selector_holdout_collection_runbook["report"],
                    selector_holdout_collection_runbook["commands_path"],
                    selector_holdout_collection_runbook["target_profile_rows_path"],
                    selector_holdout_collection_capture_audit["source"],
                    selector_holdout_collection_capture_audit["report"],
                    selector_holdout_priority_collection_capture_audit["source"],
                    selector_holdout_priority_collection_capture_audit["report"],
                    selector_holdout_priority_capture_miss["source"],
                    selector_holdout_priority_capture_miss["report"],
                    selector_holdout_blocker_status["source"],
                    selector_holdout_blocker_status["report"],
                    selector_context_trajectory_protocol["source"],
                    selector_context_trajectory_protocol["report"],
                    selector_holdout_context_worklist["source"],
                    selector_holdout_context_worklist["report"],
                    selector_holdout_context_action_plan["source"],
                    selector_holdout_context_action_plan["report"],
                    selector_holdout_target002_drift_audit["source"],
                    selector_holdout_target002_drift_audit["report"],
                    selector_holdout_target002_probe_matrix["source"],
                    selector_holdout_target002_probe_matrix["report"],
                    selector_holdout_target002_trajectory_branch["source"],
                    selector_holdout_target002_trajectory_branch["report"],
                    selector_holdout_missing_context_diagnosis["source"],
                    selector_holdout_missing_context_diagnosis["report"],
                    selector_holdout_target002_component_drift["source"],
                    selector_holdout_target002_component_drift["report"],
                    selector_component_feature_readiness["source"],
                    selector_component_feature_readiness["report"],
                    selector_component_capture_schema_contract["source"],
                    selector_component_capture_schema_contract["report"],
                    component_payload_addition_before_rows["source"],
                    component_payload_addition_before_rows["report"],
                    component_payload_selector_holdout_extension["source"],
                    component_payload_selector_holdout_extension["report"],
                    selector_context_sufficiency_gap["source"],
                    selector_context_sufficiency_gap["report"],
                    selector_pool_overlap_feature_probe["source"],
                    selector_pool_overlap_feature_probe["report"],
                    selector_context_schema_gap["source"],
                    selector_context_schema_gap["report"],
                    selector_snapshot_sample_coverage["source"],
                    selector_snapshot_sample_coverage["report"],
                    selector_next_feature_gate["source"],
                    selector_next_feature_gate["report"],
                    selector_enriched_rmp_feature_holdout["source"],
                    selector_enriched_rmp_feature_holdout["report"],
                    selector_enriched_multifeature_model_holdout["source"],
                    selector_enriched_multifeature_model_holdout["report"],
                    production_ab_entry_gate_catalog["source"],
                    production_ab_entry_gate_catalog["report"],
                    selector_threshold_frontier["source"],
                    selector_threshold_frontier["report"],
                    selector_context_collision["source"],
                    selector_context_collision["report"],
                    selector_local_feature_direction["source"],
                    selector_local_feature_direction["report"],
                    selector_context_disambiguation["source"],
                    selector_context_disambiguation["report"],
                    selector_context_scalar_candidates["source"],
                    selector_context_scalar_candidates["report"],
                    selector_context_scalar_holdout["source"],
                    selector_context_scalar_holdout["report"],
                    selector_micro_vs_fold_gate["source"],
                    selector_micro_vs_fold_gate["report"],
                    selector_model_micro_vs_fold_gate["source"],
                    selector_model_micro_vs_fold_gate["report"],
                    selector_rule_family_search["source"],
                    selector_rule_family_search["report"],
                    selector_rule_family_search_20only["source"],
                    selector_rule_family_search_20only["report"],
                    selector_rule_family_train_holdout["source"],
                    selector_rule_family_train_holdout["report"],
                    selector_rule_family_train_holdout_20only["source"],
                    selector_rule_family_train_holdout_20only["report"],
                    selector_context_fold_anatomy["source"],
                    selector_context_fold_anatomy["report"],
                    selector_context_feature_anatomy["source"],
                    selector_context_feature_anatomy["report"],
                    checks["candidate_selector_models"]["source"],
                    checks["trajectory_signal_ladder"]["source"],
                ],
                "key_metrics": {
                    "recommended_selector_candidate": checks[
                        "replay_calibrated_selector_candidate"
                    ]["recommended_selector_candidate"],
                    "exact_false_positive_count": selector_holdout[
                        "exact_false_positive_count"
                    ],
                    "exact_false_negative_count": selector_holdout[
                        "exact_false_negative_count"
                    ],
                    "broad_dataset_holdout_pass_count": selector_holdout[
                        "broad_dataset_holdout_pass_count"
                    ],
                    "broad_instance_holdout_pass_count": selector_holdout[
                        "broad_instance_holdout_pass_count"
                    ],
                    "false_positive_new_task_set_noop_count": (
                        selector_error_anatomy[
                            "false_positive_new_task_set_noop_count"
                        ]
                    ),
                    "false_negative_new_task_set_improved_count": (
                        selector_error_anatomy[
                            "false_negative_new_task_set_improved_count"
                        ]
                    ),
                    "catalog_false_positive_count": (
                        selector_counterexample_catalog["false_positive_count"]
                    ),
                    "catalog_false_negative_count": (
                        selector_counterexample_catalog["false_negative_count"]
                    ),
                    "catalog_has_new_task_set_noop_false_positive": (
                        selector_counterexample_catalog[
                            "has_new_task_set_noop_false_positive"
                        ]
                    ),
                    "catalog_has_new_task_set_improved_false_negative": (
                        selector_counterexample_catalog[
                            "has_new_task_set_improved_false_negative"
                        ]
                    ),
                    "production_selector_blocker_status": (
                        production_selector_blocker_catalog["status"]
                    ),
                    "production_selector_blocker_ids": (
                        production_selector_blocker_catalog["blocker_ids"]
                    ),
                    "selector_failure_mechanism_count": (
                        selector_failure_mechanism_audit["mechanism_count"]
                    ),
                    "selector_failure_mechanism_ids": (
                        selector_failure_mechanism_audit["mechanism_ids"]
                    ),
                    "selector_context_feature_gap_proxy_count": (
                        selector_context_feature_gap_audit["proxy_count"]
                    ),
                    "selector_context_feature_gap_proxy_ids": (
                        selector_context_feature_gap_audit["proxy_ids"]
                    ),
                    "selector_feature_availability_row_count": (
                        selector_feature_availability_audit["row_count"]
                    ),
                    "selector_feature_availability_missing_rmp_fields": (
                        selector_feature_availability_audit[
                            "desired_rmp_trajectory_missing_count"
                        ]
                    ),
                    "capture_schema_feasibility_candidate_row_count": (
                        capture_schema_feasibility_audit["candidate_row_count"]
                    ),
                    "capture_schema_feasibility_manifest_case_count": (
                        capture_schema_feasibility_audit["manifest_case_count"]
                    ),
                    "capture_schema_fields_direct_or_alias_available": (
                        capture_schema_feasibility_audit[
                            "direct_or_alias_available_field_count"
                        ]
                    ),
                    "capture_schema_fields_derivable_from_manifest": (
                        capture_schema_feasibility_audit[
                            "derivable_from_manifest_field_count"
                        ]
                    ),
                    "capture_schema_fields_recovered_from_event_history": (
                        capture_schema_feasibility_audit[
                            "recovered_from_event_history_field_count"
                        ]
                    ),
                    "capture_schema_active_basis_snapshot_metric_fields": (
                        capture_schema_feasibility_audit.get(
                            "active_basis_snapshot_metric_field_count", 0
                        )
                    ),
                    "capture_schema_fields_requiring_metric_definition": (
                        capture_schema_feasibility_audit[
                            "requires_metric_definition_count"
                        ]
                    ),
                    "capture_schema_fields_requiring_history_join": (
                        capture_schema_feasibility_audit[
                            "requires_event_history_join_count"
                        ]
                    ),
                    "capture_schema_fields_requiring_schema_extension": (
                        capture_schema_feasibility_audit[
                            "requires_capture_schema_extension_count"
                        ]
                    ),
                    "remaining_rmp_trajectory_recovery_production_ready_fields": (
                        remaining_rmp_trajectory_field_recovery[
                            "production_ready_field_count"
                        ]
                    ),
                    "remaining_rmp_trajectory_needs_metric_definition_fields": (
                        remaining_rmp_trajectory_field_recovery[
                            "needs_metric_definition_fields"
                        ]
                    ),
                    "remaining_rmp_trajectory_needs_full_active_basis_capture_fields": (
                        remaining_rmp_trajectory_field_recovery[
                            "needs_full_active_basis_capture_fields"
                        ]
                    ),
                    "active_basis_exact_churn_reconstructable_case_count": (
                        active_basis_observability_gap[
                            "exact_active_basis_churn_reconstructable_case_count"
                        ]
                    ),
                    "active_basis_exact_degeneracy_reconstructable_case_count": (
                        active_basis_observability_gap[
                            "exact_rmp_degeneracy_pressure_reconstructable_case_count"
                        ]
                    ),
                    "active_basis_proxy_context_folds": (
                        active_basis_observability_gap[
                            "active_basis_proxy_context_folds"
                        ]
                    ),
                    "degeneracy_proxy_context_folds": (
                        active_basis_observability_gap[
                            "degeneracy_proxy_context_folds"
                        ]
                    ),
                    "active_basis_capture_schema_feasible_fields": (
                        active_basis_capture_schema_feasibility[
                            "feasible_target_schema_field_count"
                        ]
                    ),
                    "active_basis_capture_schema_missing_fields": (
                        active_basis_capture_schema_feasibility[
                            "missing_target_schema_field_count"
                        ]
                    ),
                    "active_basis_capture_requires_solver_model_change": (
                        active_basis_capture_schema_feasibility[
                            "requires_solver_model_change"
                        ]
                    ),
                    "active_basis_capture_requires_certificate_effect": (
                        active_basis_capture_schema_feasibility[
                            "requires_certificate_effect"
                        ]
                    ),
                    "active_basis_capture_supports_active_basis_snapshot": (
                        active_basis_capture_schema_feasibility[
                            "counterfactual_capture_supports_active_basis_snapshot"
                        ]
                    ),
                    "active_basis_capture_schema_implementation_status": (
                        active_basis_capture_schema_feasibility[
                            "capture_schema_implementation_status"
                        ]
                    ),
                    "active_basis_snapshot_smoke_candidate_rows": (
                        active_basis_snapshot_smoke["impact_candidate_row_count"]
                    ),
                    "active_basis_snapshot_smoke_churn_nonempty": (
                        active_basis_snapshot_smoke[
                            "active_basis_churn_nonempty_count"
                        ]
                    ),
                    "active_basis_snapshot_smoke_degeneracy_nonempty": (
                        active_basis_snapshot_smoke[
                            "rmp_degeneracy_pressure_nonempty_count"
                        ]
                    ),
                    "active_basis_snapshot_smoke_official_effect_count": (
                        active_basis_snapshot_smoke["official_effect_count"]
                    ),
                    "active_basis_snapshot_mt20_smoke_candidate_rows": (
                        active_basis_snapshot_mt20_smoke[
                            "impact_candidate_row_count"
                        ]
                    ),
                    "active_basis_snapshot_mt20_smoke_high_impact": (
                        active_basis_snapshot_mt20_smoke[
                            "impact_high_impact_candidate_count"
                        ]
                    ),
                    "active_basis_snapshot_mt20_smoke_noop": (
                        active_basis_snapshot_mt20_smoke[
                            "impact_noop_candidate_count"
                        ]
                    ),
                    "active_basis_snapshot_mt20_smoke_payload_max": (
                        active_basis_snapshot_mt20_smoke[
                            "active_basis_payload_count_max"
                        ]
                    ),
                    "active_basis_snapshot_mt20_smoke_official_effect_count": (
                        active_basis_snapshot_mt20_smoke["official_effect_count"]
                    ),
                    "active_basis_snapshot_multi20_smoke_candidate_rows": (
                        active_basis_snapshot_multi20_smoke[
                            "impact_candidate_row_count"
                        ]
                    ),
                    "active_basis_snapshot_multi20_smoke_high_impact": (
                        active_basis_snapshot_multi20_smoke[
                            "impact_high_impact_candidate_count"
                        ]
                    ),
                    "active_basis_snapshot_multi20_smoke_noop": (
                        active_basis_snapshot_multi20_smoke[
                            "impact_noop_candidate_count"
                        ]
                    ),
                    "active_basis_snapshot_multi20_smoke_payload_min": (
                        active_basis_snapshot_multi20_smoke[
                            "active_basis_payload_count_min"
                        ]
                    ),
                    "active_basis_snapshot_multi20_smoke_official_effect_count": (
                        active_basis_snapshot_multi20_smoke[
                            "official_effect_count"
                        ]
                    ),
                    "active_basis_snapshot_greedy_apollo20_02_smoke_candidate_rows": (
                        active_basis_snapshot_greedy_apollo20_02_smoke[
                            "impact_candidate_row_count"
                        ]
                    ),
                    "active_basis_snapshot_greedy_apollo20_02_smoke_high_impact": (
                        active_basis_snapshot_greedy_apollo20_02_smoke[
                            "impact_high_impact_candidate_count"
                        ]
                    ),
                    "active_basis_snapshot_greedy_apollo20_02_smoke_noop": (
                        active_basis_snapshot_greedy_apollo20_02_smoke[
                            "impact_noop_candidate_count"
                        ]
                    ),
                    "active_basis_snapshot_greedy_apollo20_02_smoke_official_effect_count": (
                        active_basis_snapshot_greedy_apollo20_02_smoke[
                            "official_effect_count"
                        ]
                    ),
                    "active_basis_snapshot_greedy20_pair_smoke_candidate_rows": (
                        active_basis_snapshot_greedy20_pair_smoke[
                            "impact_candidate_row_count"
                        ]
                    ),
                    "active_basis_snapshot_greedy20_pair_smoke_high_impact": (
                        active_basis_snapshot_greedy20_pair_smoke[
                            "impact_high_impact_candidate_count"
                        ]
                    ),
                    "active_basis_snapshot_greedy20_pair_smoke_noop": (
                        active_basis_snapshot_greedy20_pair_smoke[
                            "impact_noop_candidate_count"
                        ]
                    ),
                    "active_basis_snapshot_greedy20_pair_smoke_official_effect_count": (
                        active_basis_snapshot_greedy20_pair_smoke[
                            "official_effect_count"
                        ]
                    ),
                    "active_basis_snapshot_selector_signal_row_count": (
                        active_basis_snapshot_selector_signal["row_count"]
                    ),
                    "active_basis_snapshot_selector_signal_task20_row_count": (
                        active_basis_snapshot_selector_signal["task20_row_count"]
                    ),
                    "active_basis_snapshot_selector_signal_task20_true_rc_threshold_fp": (
                        active_basis_snapshot_selector_signal[
                            "task20_true_rc_threshold_fp"
                        ]
                    ),
                    "active_basis_snapshot_selector_signal_perfect_single_feature_rule_count": (
                        active_basis_snapshot_selector_signal[
                            "perfect_single_feature_rule_count"
                        ]
                    ),
                    "active_basis_snapshot_counterexamples_task20_row_count": (
                        active_basis_snapshot_counterexamples["task20_row_count"]
                    ),
                    "active_basis_snapshot_counterexamples_false_positive_count": (
                        active_basis_snapshot_counterexamples["false_positive_count"]
                    ),
                    "active_basis_snapshot_counterexamples_strongest_noop_true_reduced_cost": (
                        active_basis_snapshot_counterexamples[
                            "strongest_noop_true_reduced_cost"
                        ]
                    ),
                    "active_basis_snapshot_counterexamples_weaker_improved_than_strongest_noop_count": (
                        active_basis_snapshot_counterexamples[
                            "weaker_improved_than_strongest_noop_count"
                        ]
                    ),
                    "active_basis_snapshot_counterexamples_mixed_instance_group_count": (
                        active_basis_snapshot_counterexamples[
                            "mixed_instance_group_count"
                        ]
                    ),
                    "selector_collection_schema_row_count": (
                        selector_collection_schema_coverage["row_count"]
                    ),
                    "selector_collection_schema_journey_missing_count": (
                        selector_collection_schema_coverage[
                            "journey_missing_count"
                        ]
                    ),
                    "selector_collection_schema_incomplete_journey_count": (
                        selector_collection_schema_coverage[
                            "incomplete_journey_count"
                        ]
                    ),
                    "selector_collection_schema_signature_present_count": (
                        selector_collection_schema_coverage[
                            "signature_present_count"
                        ]
                    ),
                    "selector_collection_schema_official_effect_event_bad_count": (
                        selector_collection_schema_coverage[
                            "official_effect_event_bad_count"
                        ]
                    ),
                    "selector_holdout_collection_target_count": (
                        selector_holdout_collection_manifest[
                            "collection_target_count"
                        ]
                    ),
                    "selector_holdout_collection_candidate_row_count": (
                        selector_holdout_collection_manifest[
                            "collection_target_candidate_row_count"
                        ]
                    ),
                    "selector_holdout_targets_needing_active_basis_snapshot_count": (
                        selector_holdout_collection_manifest[
                            "targets_needing_active_basis_snapshot_count"
                        ]
                    ),
                    "selector_holdout_existing_active_basis_snapshot_anchor_count": (
                        selector_holdout_collection_manifest[
                            "existing_active_basis_snapshot_anchor_count"
                        ]
                    ),
                    "selector_holdout_collection_runbook_command_count": (
                        selector_holdout_collection_runbook["command_count"]
                    ),
                    "selector_holdout_collection_runbook_source_profile_count": (
                        selector_holdout_collection_runbook["source_profile_count"]
                    ),
                    "selector_holdout_collection_runbook_source_config_class_count": (
                        selector_holdout_collection_runbook[
                            "source_config_class_count"
                        ]
                    ),
                    "selector_holdout_collection_runbook_instance_count": (
                        selector_holdout_collection_runbook["instance_count"]
                    ),
                    "selector_holdout_collection_runbook_unresolved_instances": (
                        selector_holdout_collection_runbook["unresolved_instances"]
                    ),
                    "selector_holdout_collection_runbook_unsupported_profiles": (
                        selector_holdout_collection_runbook["unsupported_profiles"]
                    ),
                    "selector_holdout_collection_runbook_unsupported_source_configs": (
                        selector_holdout_collection_runbook[
                            "unsupported_source_configs"
                        ]
                    ),
                    "selector_holdout_collection_capture_event_count": (
                        selector_holdout_collection_capture_audit[
                            "capture_event_count"
                        ]
                    ),
                    "selector_holdout_collection_expected_context_hash_count": (
                        selector_holdout_collection_capture_audit[
                            "expected_context_hash_count"
                        ]
                    ),
                    "selector_holdout_collection_expected_context_hit_count": (
                        selector_holdout_collection_capture_audit[
                            "expected_context_hit_count"
                        ]
                    ),
                    "selector_holdout_collection_expected_context_complete_hit_count": (
                        selector_holdout_collection_capture_audit[
                            "expected_context_complete_hit_count"
                        ]
                    ),
                    "selector_holdout_collection_missing_expected_context_count": (
                        selector_holdout_collection_capture_audit[
                            "missing_expected_context_count"
                        ]
                    ),
                    "selector_holdout_collection_ready_for_selector_holdout": (
                        selector_holdout_collection_capture_audit[
                            "ready_for_selector_holdout"
                        ]
                    ),
                    "selector_holdout_collection_no_certificate_bad_count": (
                        selector_holdout_collection_capture_audit[
                            "no_certificate_bad_count"
                        ]
                    ),
                    "selector_holdout_collection_active_basis_bad_count": (
                        selector_holdout_collection_capture_audit[
                            "active_basis_bad_count"
                        ]
                    ),
                    "selector_holdout_priority_collection_capture_event_count": (
                        selector_holdout_priority_collection_capture_audit[
                            "capture_event_count"
                        ]
                    ),
                    "selector_holdout_priority_collection_expected_context_hash_count": (
                        selector_holdout_priority_collection_capture_audit[
                            "expected_context_hash_count"
                        ]
                    ),
                    "selector_holdout_priority_collection_expected_context_hit_count": (
                        selector_holdout_priority_collection_capture_audit[
                            "expected_context_hit_count"
                        ]
                    ),
                    "selector_holdout_priority_collection_missing_expected_context_count": (
                        selector_holdout_priority_collection_capture_audit[
                            "missing_expected_context_count"
                        ]
                    ),
                    "selector_holdout_priority_collection_ready_for_selector_holdout": (
                        selector_holdout_priority_collection_capture_audit[
                            "ready_for_selector_holdout"
                        ]
                    ),
                    "selector_holdout_priority_collection_no_certificate_bad_count": (
                        selector_holdout_priority_collection_capture_audit[
                            "no_certificate_bad_count"
                        ]
                    ),
                    "selector_holdout_priority_collection_active_basis_bad_count": (
                        selector_holdout_priority_collection_capture_audit[
                            "active_basis_bad_count"
                        ]
                    ),
                    "selector_holdout_priority_capture_miss_expected_context_count": (
                        selector_holdout_priority_capture_miss[
                            "expected_context_count"
                        ]
                    ),
                    "selector_holdout_priority_capture_miss_exact_hit_context_count": (
                        selector_holdout_priority_capture_miss[
                            "exact_hit_context_count"
                        ]
                    ),
                    "selector_holdout_priority_capture_miss_source_active_hash_missing_context_count": (
                        selector_holdout_priority_capture_miss[
                            "source_active_hash_missing_context_count"
                        ]
                    ),
                    "selector_holdout_priority_capture_miss_same_active_component_drift_context_count": (
                        selector_holdout_priority_capture_miss[
                            "same_active_component_drift_context_count"
                        ]
                    ),
                    "selector_holdout_blocker_collection_expected_context_hit_count": (
                        selector_holdout_blocker_status[
                            "collection_expected_context_hit_count"
                        ]
                    ),
                    "selector_holdout_blocker_priority_expected_context_hit_count": (
                        selector_holdout_blocker_status[
                            "priority_expected_context_hit_count"
                        ]
                    ),
                    "selector_holdout_blocker_complete_snapshot_label_counts": (
                        selector_holdout_blocker_status[
                            "complete_snapshot_label_counts"
                        ]
                    ),
                    "selector_holdout_blocker_complete_explicit_forbidden_label_counts": (
                        selector_holdout_blocker_status[
                            "complete_explicit_forbidden_label_counts"
                        ]
                    ),
                    "selector_context_trajectory_protocol_status": (
                        selector_context_trajectory_protocol["status"]
                    ),
                    "selector_context_trajectory_protocol_exact_context_component_count": (
                        selector_context_trajectory_protocol[
                            "exact_context_component_count"
                        ]
                    ),
                    "selector_context_trajectory_protocol_required_capture_payload_count": (
                        selector_context_trajectory_protocol[
                            "required_capture_payload_count"
                        ]
                    ),
                    "selector_context_trajectory_protocol_source_profile_rerun_is_not_sufficient": (
                        selector_context_trajectory_protocol[
                            "source_profile_rerun_is_not_sufficient"
                        ]
                    ),
                    "selector_context_trajectory_protocol_same_active_hash_is_not_sufficient": (
                        selector_context_trajectory_protocol[
                            "same_active_hash_is_not_sufficient"
                        ]
                    ),
                    "selector_holdout_context_worklist_unresolved_context_count": (
                        selector_holdout_context_worklist[
                            "unresolved_context_count"
                        ]
                    ),
                    "selector_holdout_context_worklist_actionable_context_count": (
                        selector_holdout_context_worklist[
                            "actionable_context_count"
                        ]
                    ),
                    "selector_holdout_context_worklist_priority_miss_class_counts": (
                        selector_holdout_context_worklist[
                            "priority_miss_class_counts"
                        ]
                    ),
                    "selector_holdout_context_action_unresolved_action_count": (
                        selector_holdout_context_action_plan[
                            "unresolved_action_count"
                        ]
                    ),
                    "selector_holdout_context_action_unresolved_with_command_count": (
                        selector_holdout_context_action_plan[
                            "unresolved_with_command_count"
                        ]
                    ),
                    "selector_holdout_context_action_unresolved_without_command_count": (
                        selector_holdout_context_action_plan[
                            "unresolved_without_command_count"
                        ]
                    ),
                    "selector_holdout_context_action_unresolved_execution_category_counts": (
                        selector_holdout_context_action_plan[
                            "unresolved_execution_category_counts"
                        ]
                    ),
                    "selector_holdout_target002_drift_target_context_hash": (
                        selector_holdout_target002_drift_audit[
                            "target_context_hash"
                        ]
                    ),
                    "selector_holdout_target002_drift_target_active_hash": (
                        selector_holdout_target002_drift_audit[
                            "target_active_hash"
                        ]
                    ),
                    "selector_holdout_target002_drift_source_target_hit_count": (
                        selector_holdout_target002_drift_audit[
                            "source_target_hit_count"
                        ]
                    ),
                    "selector_holdout_target002_drift_new_target_hit_count": (
                        selector_holdout_target002_drift_audit[
                            "new_target_hit_count"
                        ]
                    ),
                    "selector_holdout_target002_drift_new_same_active_event_count": (
                        selector_holdout_target002_drift_audit[
                            "new_same_active_event_count"
                        ]
                    ),
                    "selector_holdout_target002_drift_new_same_active_found_negative_count": (
                        selector_holdout_target002_drift_audit[
                            "new_same_active_found_negative_count"
                        ]
                    ),
                    "selector_holdout_target002_drift_new_same_active_incomplete_count": (
                        selector_holdout_target002_drift_audit[
                            "new_same_active_incomplete_count"
                        ]
                    ),
                    "selector_holdout_target002_probe_matrix_probe_count": (
                        selector_holdout_target002_probe_matrix["probe_count"]
                    ),
                    "selector_holdout_target002_probe_matrix_reproduction_probe_count": (
                        selector_holdout_target002_probe_matrix[
                            "reproduction_probe_count"
                        ]
                    ),
                    "selector_holdout_target002_probe_matrix_source_target_hit_count": (
                        selector_holdout_target002_probe_matrix[
                            "source_target_hit_count"
                        ]
                    ),
                    "selector_holdout_target002_probe_matrix_target_recovered_probe_count": (
                        selector_holdout_target002_probe_matrix[
                            "target_recovered_probe_count"
                        ]
                    ),
                    "selector_holdout_target002_trajectory_branch_same_active_event_count": (
                        selector_holdout_target002_trajectory_branch[
                            "same_active_event_count"
                        ]
                    ),
                    "selector_holdout_target002_trajectory_branch_non_source_same_active_event_count": (
                        selector_holdout_target002_trajectory_branch[
                            "non_source_same_active_event_count"
                        ]
                    ),
                    "selector_holdout_target002_trajectory_branch_same_active_context_hashes": (
                        selector_holdout_target002_trajectory_branch[
                            "same_active_context_hashes"
                        ]
                    ),
                    "selector_context_sufficiency_status": (
                        selector_context_sufficiency_gap["selector_context_status"]
                    ),
                    "selector_context_sufficiency_exact_disambiguator_fields_present_any": (
                        selector_context_sufficiency_gap[
                            "exact_disambiguator_fields_present_any"
                        ]
                    ),
                    "selector_context_sufficiency_robust_single_feature_selector_count": (
                        selector_context_sufficiency_gap[
                            "robust_single_feature_selector_count"
                        ]
                    ),
                    "selector_context_sufficiency_robust_multifeature_model_count": (
                        selector_context_sufficiency_gap[
                            "robust_multifeature_model_count"
                        ]
                    ),
                    "selector_context_sufficiency_required_next_feature_families": (
                        selector_context_sufficiency_gap[
                            "required_next_feature_families"
                        ]
                    ),
                    "selector_pool_overlap_row_count": (
                        selector_pool_overlap_feature_probe["row_count"]
                    ),
                    "selector_pool_overlap_derived_feature_count": (
                        selector_pool_overlap_feature_probe["derived_feature_count"]
                    ),
                    "selector_pool_overlap_robust_derived_feature_count": (
                        selector_pool_overlap_feature_probe[
                            "robust_all_holdout_derived_feature_count"
                        ]
                    ),
                    "selector_pool_overlap_robust_model_count": (
                        selector_pool_overlap_feature_probe[
                            "robust_all_holdout_model_count"
                        ]
                    ),
                    "selector_pool_overlap_best_context_model": (
                        selector_pool_overlap_feature_probe["best_context_model"]
                    ),
                    "selector_pool_overlap_best_context_model_context_folds": (
                        selector_pool_overlap_feature_probe[
                            "best_context_model_context_folds"
                        ]
                    ),
                    "selector_pool_overlap_explicit_forbidden_signature_list_available_count": (
                        selector_pool_overlap_feature_probe[
                            "explicit_forbidden_signature_list_available_count"
                        ]
                    ),
                    "selector_component_capture_event_count": (
                        selector_component_capture_schema_contract[
                            "capture_event_count"
                        ]
                    ),
                    "selector_component_capture_complete_active_basis_events": (
                        selector_component_capture_schema_contract[
                            "complete_active_basis_events"
                        ]
                    ),
                    "selector_component_capture_complete_pool_events": (
                        selector_component_capture_schema_contract[
                            "complete_pool_events"
                        ]
                    ),
                    "selector_component_capture_returned_batch_complete_events": (
                        selector_component_capture_schema_contract[
                            "returned_batch_complete_events"
                        ]
                    ),
                    "selector_component_capture_forbidden_explicit_events": (
                        selector_component_capture_schema_contract[
                            "forbidden_explicit_events"
                        ]
                    ),
                    "selector_component_capture_code_supports_explicit_forbidden_payload": (
                        selector_component_capture_schema_contract[
                            "code_supports_explicit_forbidden_payload"
                        ]
                    ),
                    "selector_component_capture_runbook_enables_explicit_forbidden_payload": (
                        selector_component_capture_schema_contract[
                            "holdout_runbook_enables_explicit_forbidden_payload"
                        ]
                    ),
                    "component_payload_rows_candidate_row_count": (
                        component_payload_addition_before_rows["candidate_row_count"]
                    ),
                    "component_payload_rows_ready_case_count": (
                        component_payload_addition_before_rows["ready_case_count"]
                    ),
                    "component_payload_rows_high_impact_candidate_count": (
                        component_payload_addition_before_rows[
                            "high_impact_candidate_count"
                        ]
                    ),
                    "component_payload_rows_noop_candidate_count": (
                        component_payload_addition_before_rows["noop_candidate_count"]
                    ),
                    "component_payload_rows_explicit_forbidden_true_count": (
                        component_payload_addition_before_rows[
                            "explicit_forbidden_true_count"
                        ]
                    ),
                    "component_payload_rows_runs_local_rmp_replay": (
                        component_payload_addition_before_rows[
                            "runs_local_rmp_replay"
                        ]
                    ),
                    "component_payload_selector_extension_base_row_count": (
                        component_payload_selector_holdout_extension[
                            "base_row_count"
                        ]
                    ),
                    "component_payload_selector_extension_component_row_count": (
                        component_payload_selector_holdout_extension[
                            "component_row_count"
                        ]
                    ),
                    "component_payload_selector_extension_combined_row_count": (
                        component_payload_selector_holdout_extension[
                            "combined_row_count"
                        ]
                    ),
                    "component_payload_selector_extension_component_positive_only": (
                        component_payload_selector_holdout_extension[
                            "component_positive_only"
                        ]
                    ),
                    "component_payload_selector_extension_combined_robust_feature_count": (
                        component_payload_selector_holdout_extension[
                            "combined_robust_all_holdout_derived_feature_count"
                        ]
                    ),
                    "component_payload_selector_extension_combined_robust_model_count": (
                        component_payload_selector_holdout_extension[
                            "combined_robust_all_holdout_model_count"
                        ]
                    ),
                    "component_payload_selector_extension_combined_best_context_folds": (
                        component_payload_selector_holdout_extension[
                            "combined_best_context_model_context_folds"
                        ]
                    ),
                    "selector_context_schema_gap_candidate_row_count": (
                        selector_context_schema_gap["candidate_row_count"]
                    ),
                    "selector_context_schema_gap_manifest_case_count": (
                        selector_context_schema_gap["manifest_case_count"]
                    ),
                    "selector_context_schema_gap_active_basis_snapshot_complete_true_count": (
                        selector_context_schema_gap[
                            "active_basis_snapshot_complete_true_count"
                        ]
                    ),
                    "selector_context_schema_gap_explicit_forbidden_signature_list_count": (
                        selector_context_schema_gap[
                            "cases_with_explicit_forbidden_signature_list"
                        ]
                    ),
                    "selector_context_schema_gap_feature_family_status": (
                        selector_context_schema_gap["feature_family_status"]
                    ),
                    "selector_snapshot_sample_coverage_candidate_row_count": (
                        selector_snapshot_sample_coverage["candidate_row_count"]
                    ),
                    "selector_snapshot_sample_coverage_complete_snapshot_row_count": (
                        selector_snapshot_sample_coverage[
                            "complete_snapshot_row_count"
                        ]
                    ),
                    "selector_snapshot_sample_coverage_combined_replay_complete_snapshot_row_count": (
                        selector_snapshot_sample_coverage[
                            "combined_replay_selector_complete_snapshot_row_count"
                        ]
                    ),
                    "selector_snapshot_sample_coverage_holdout_ready": (
                        selector_snapshot_sample_coverage["holdout_ready"]
                    ),
                    "selector_next_feature_gate_status": (
                        selector_next_feature_gate[
                            "selector_next_feature_gate_status"
                        ]
                    ),
                    "selector_next_feature_gate_blocked_feature_families": (
                        selector_next_feature_gate["blocked_feature_families"]
                    ),
                    "selector_next_feature_gate_forbidden_next_actions": (
                        selector_next_feature_gate["forbidden_next_actions"]
                    ),
                    "selector_next_feature_gate_allowed_next_actions": (
                        selector_next_feature_gate["allowed_next_actions"]
                    ),
                    "selector_enriched_rmp_holdout_robust_numeric_features": (
                        selector_enriched_rmp_feature_holdout[
                            "robust_all_holdout_numeric_feature_count"
                        ]
                    ),
                    "selector_enriched_rmp_holdout_robust_enriched_features": (
                        selector_enriched_rmp_feature_holdout[
                            "robust_all_holdout_enriched_feature_count"
                        ]
                    ),
                    "selector_enriched_rmp_holdout_dual_l1_context_folds": (
                        selector_enriched_rmp_feature_holdout[
                            "dual_l1_context_passing_folds"
                        ]
                    ),
                    "selector_enriched_rmp_holdout_control_context_folds": (
                        selector_enriched_rmp_feature_holdout[
                            "control_objective_context_passing_folds"
                        ]
                    ),
                    "selector_enriched_multifeature_robust_model_count": (
                        selector_enriched_multifeature_model_holdout[
                            "robust_all_holdout_model_count"
                        ]
                    ),
                    "selector_enriched_multifeature_best_model": (
                        selector_enriched_multifeature_model_holdout[
                            "best_context_model"
                        ]
                    ),
                    "selector_enriched_multifeature_best_context_folds": (
                        selector_enriched_multifeature_model_holdout[
                            "best_context_model_context_folds"
                        ]
                    ),
                    "selector_enriched_multifeature_best_instance_folds": (
                        selector_enriched_multifeature_model_holdout[
                            "best_context_model_instance_folds"
                        ]
                    ),
                    "selector_enriched_multifeature_best_dataset_folds": (
                        selector_enriched_multifeature_model_holdout[
                            "best_context_model_dataset_folds"
                        ]
                    ),
                    "production_ab_entry_status": (
                        production_ab_entry_gate_catalog["status"]
                    ),
                    "production_ab_entry_gate_blockers": (
                        production_ab_entry_gate_catalog["entry_gate_blockers"]
                    ),
                    "production_ab_must_not_enable_worker_default": (
                        production_ab_entry_gate_catalog[
                            "must_not_enable_worker_default"
                        ]
                    ),
                    "production_ab_must_not_open_certificate_gate": (
                        production_ab_entry_gate_catalog[
                            "must_not_open_certificate_gate"
                        ]
                    ),
                    "perfect_true_rc_threshold_count": (
                        selector_threshold_frontier["perfect_threshold_count"]
                    ),
                    "zero_false_positive_best_recall": (
                        selector_threshold_frontier["zero_fp_recall"]
                    ),
                    "zero_false_negative_false_positive_count": (
                        selector_threshold_frontier["zero_fn_fp"]
                    ),
                    "task_set_mixed_group_count": (
                        selector_context_collision["task_set_mixed_group_count"]
                    ),
                    "task_sequence_mixed_group_count": (
                        selector_context_collision[
                            "task_sequence_mixed_group_count"
                        ]
                    ),
                    "online_flags_mixed_row_count": (
                        selector_context_collision["online_flags_mixed_row_count"]
                    ),
                    "task_set_true_rc_improved_lower_count": (
                        selector_local_feature_direction[
                            "task_set_true_rc_improved_lower_count"
                        ]
                    ),
                    "task_set_true_rc_noop_lower_count": (
                        selector_local_feature_direction[
                            "task_set_true_rc_noop_lower_count"
                        ]
                    ),
                    "task_sequence_true_rc_improved_lower_count": (
                        selector_local_feature_direction[
                            "task_sequence_true_rc_improved_lower_count"
                        ]
                    ),
                    "task_sequence_true_rc_noop_lower_count": (
                        selector_local_feature_direction[
                            "task_sequence_true_rc_noop_lower_count"
                        ]
                    ),
                    "context_disambiguation_local_sequence_mixed_group_count": (
                        selector_context_disambiguation[
                            "local_sequence_mixed_group_count"
                        ]
                    ),
                    "context_disambiguation_online_instance_mixed_group_count": (
                        selector_context_disambiguation[
                            "online_instance_mixed_group_count"
                        ]
                    ),
                    "context_disambiguation_dataset_mixed_group_count": (
                        selector_context_disambiguation["dataset_mixed_group_count"]
                    ),
                    "context_disambiguation_context_hash_mixed_group_count": (
                        selector_context_disambiguation[
                            "context_hash_mixed_group_count"
                        ]
                    ),
                    "context_scalar_control_objective_bin_100_mixed_group_count": (
                        selector_context_scalar_candidates[
                            "control_objective_bin_100_mixed_group_count"
                        ]
                    ),
                    "context_scalar_control_objective_bin_100_group_count": (
                        selector_context_scalar_candidates[
                            "control_objective_bin_100_group_count"
                        ]
                    ),
                    "context_scalar_cheap_scalar_mixed_group_count": (
                        selector_context_scalar_candidates[
                            "cheap_scalar_mixed_group_count"
                        ]
                    ),
                    "context_scalar_holdout_passing_model_count": (
                        selector_context_scalar_holdout["passing_model_count"]
                    ),
                    "context_scalar_holdout_threshold_context_precision": (
                        selector_context_scalar_holdout[
                            "threshold_context_precision"
                        ]
                    ),
                    "context_scalar_holdout_bin100_context_recall": (
                        selector_context_scalar_holdout["bin100_context_recall"]
                    ),
                    "micro_vs_fold_robust_all_fold_passing_feature_count": (
                        selector_micro_vs_fold_gate[
                            "robust_all_fold_passing_feature_count"
                        ]
                    ),
                    "micro_vs_fold_true_rc_context_passing_folds": (
                        f"{selector_micro_vs_fold_gate['true_rc_context_passing_fold_count']}/"
                        f"{selector_micro_vs_fold_gate['true_rc_context_fold_count']}"
                    ),
                    "micro_vs_fold_new_task_set_dataset_passing_folds": (
                        f"{selector_micro_vs_fold_gate['new_task_set_dataset_passing_fold_count']}/"
                        f"{selector_micro_vs_fold_gate['new_task_set_dataset_fold_count']}"
                    ),
                    "model_micro_vs_fold_robust_all_fold_passing_model_count": (
                        selector_model_micro_vs_fold_gate[
                            "robust_all_fold_passing_model_count"
                        ]
                    ),
                    "model_micro_vs_fold_nearest_context_passing_folds": (
                        f"{selector_model_micro_vs_fold_gate['nearest_context_passing_fold_count']}/"
                        f"{selector_model_micro_vs_fold_gate['nearest_context_fold_count']}"
                    ),
                    "model_micro_vs_fold_shallow_dataset_passing_folds": (
                        f"{selector_model_micro_vs_fold_gate['shallow_dataset_passing_fold_count']}/"
                        f"{selector_model_micro_vs_fold_gate['shallow_dataset_fold_count']}"
                    ),
                    "rule_family_rule_count": (
                        selector_rule_family_search["rule_count"]
                    ),
                    "rule_family_material_all_fold_passing_rule_count": (
                        selector_rule_family_search[
                            "material_all_fold_passing_rule_count"
                        ]
                    ),
                    "rule_family_best_rule_precision": (
                        selector_rule_family_search["best_rule_precision"]
                    ),
                    "rule_family_best_rule_recall": (
                        selector_rule_family_search["best_rule_recall"]
                    ),
                    "rule_family_20only_rule_count": (
                        selector_rule_family_search_20only["rule_count"]
                    ),
                    "rule_family_20only_material_all_fold_passing_rule_count": (
                        selector_rule_family_search_20only[
                            "material_all_fold_passing_rule_count"
                        ]
                    ),
                    "rule_family_20only_best_rule_precision": (
                        selector_rule_family_search_20only["best_rule_precision"]
                    ),
                    "rule_family_20only_best_rule_recall": (
                        selector_rule_family_search_20only["best_rule_recall"]
                    ),
                    "rule_family_train_context_material_passing_folds": (
                        f"{selector_rule_family_train_holdout['context_material_passing_fold_count']}/"
                        f"{selector_rule_family_train_holdout['context_fold_count']}"
                    ),
                    "rule_family_train_20only_context_material_passing_folds": (
                        f"{selector_rule_family_train_holdout_20only['context_material_passing_fold_count']}/"
                        f"{selector_rule_family_train_holdout_20only['context_fold_count']}"
                    ),
                    "context_fold_anatomy_twenty_false_positive_no_positive_context_count": (
                        selector_context_fold_anatomy[
                            "twenty_false_positive_no_positive_context_count"
                        ]
                    ),
                    "context_fold_anatomy_twenty_missed_positive_context_count": (
                        selector_context_fold_anatomy[
                            "twenty_missed_positive_context_count"
                        ]
                    ),
                    "context_fold_anatomy_twenty_mixed_failure_context_count": (
                        selector_context_fold_anatomy[
                            "twenty_mixed_failure_context_count"
                        ]
                    ),
                    "context_feature_mixed_instance_group_count": (
                        selector_context_feature_anatomy[
                            "mixed_instance_group_count"
                        ]
                    ),
                    "context_feature_mixed_dataset_group_count": (
                        selector_context_feature_anatomy[
                            "mixed_dataset_group_count"
                        ]
                    ),
                    "context_feature_false_positive_no_positive_context_count": (
                        selector_context_feature_anatomy[
                            "false_positive_no_positive_context_count"
                        ]
                    ),
                    "context_feature_missed_positive_context_count": (
                        selector_context_feature_anatomy[
                            "missed_positive_context_count"
                        ]
                    ),
                },
            },
            {
                "conclusion_id": "exact_context_capture_ready_but_calibration_only",
                "status": "supported_not_production",
                "summary": (
                    "Capture/replay data are ready for selector calibration, "
                    "not for production selector or certificate effect."
                ),
                "primary_artifacts": [
                    exact_capture_status["source"],
                    exact_capture_status["report"],
                    code_boundary["source"],
                    code_boundary["report"],
                    active_basis_snapshot_smoke["source"],
                    active_basis_snapshot_smoke["report"],
                ],
                "key_metrics": {
                    "ready_case_count": exact_capture_status["ready_case_count"],
                    "candidate_row_count": exact_capture_status[
                        "candidate_row_count"
                    ],
                    "high_impact_candidate_count": exact_capture_status[
                        "high_impact_candidate_count"
                    ],
                    "noop_candidate_count": exact_capture_status[
                        "noop_candidate_count"
                    ],
                    "production_validated_selector": exact_capture_status[
                        "production_validated_selector"
                    ],
                    "counterfactual_capture_guarded_by_config": (
                        code_boundary["counterfactual_capture_guarded_by_config"]
                    ),
                    "counterfactual_capture_diagnostic_only": (
                        code_boundary["counterfactual_capture_diagnostic_only"]
                    ),
                    "counterfactual_capture_default_enabled": (
                        code_boundary["counterfactual_capture_default_enabled"]
                    ),
                    "counterfactual_capture_official_bound_effect": (
                        code_boundary[
                            "counterfactual_capture_official_bound_effect"
                        ]
                    ),
                    "active_basis_snapshot_smoke_all_checks_pass": (
                        active_basis_snapshot_smoke[
                            "check_active_basis_snapshot_smoke_is_current"
                        ]
                    ),
                    "active_basis_snapshot_smoke_official_effect_count": (
                        active_basis_snapshot_smoke["official_effect_count"]
                    ),
                    "profile_priority_defaults_empty": (
                        code_boundary["profile_priority_defaults_empty"]
                    ),
                    "experimental_profiles_not_default": (
                        code_boundary["experimental_profiles_not_default"]
                    ),
                    "mainline_unvalidated_effect_default_enabled": (
                        code_boundary[
                            "mainline_unvalidated_effect_default_enabled"
                        ]
                    ),
                },
            },
            {
                "conclusion_id": "objective_completion_blocked",
                "status": "blocking",
                "summary": (
                    "The user objective remains active because production selector "
                    "validation and 20-task speedup evidence are missing."
                ),
                "primary_artifacts": [
                    str(DEFAULT_OUTPUT_DIR / "summary.json"),
                    str(ROOT_CAUSE_DIAGNOSIS_REPORT),
                    str(GOAL_COMPLETION_BLOCKERS_REPORT),
                    str(WHY_MANY_ATTEMPTS_FAILED_SUMMARY),
                    str(WHY_MANY_ATTEMPTS_FAILED_REPORT),
                    root_cause_causal_chain_audit["source"],
                    root_cause_causal_chain_audit["report"],
                    str(ROOT_CAUSE_CURRENT_ANSWER_SUMMARY),
                    str(ROOT_CAUSE_CURRENT_ANSWER_REPORT),
                    stale_claims["source"],
                    stale_claims["report"],
                    missing_requirement_evidence_scan["source"],
                    missing_requirement_evidence_scan["report"],
                    str(ROOT_CAUSE_NEXT_ACTION_PLAN_SUMMARY),
                    str(ROOT_CAUSE_NEXT_ACTION_PLAN_REPORT),
                    str(ROOT_CAUSE_SELECTOR_COLLECTION_PLAN_SUMMARY),
                    str(ROOT_CAUSE_SELECTOR_COLLECTION_PLAN_REPORT),
                    str(ROOT_CAUSE_SELECTOR_COLLECTION_SCHEMA_COVERAGE_SUMMARY),
                    str(ROOT_CAUSE_SELECTOR_COLLECTION_SCHEMA_COVERAGE_REPORT),
                    str(ROOT_CAUSE_SELECTOR_HOLDOUT_COLLECTION_MANIFEST_SUMMARY),
                    str(ROOT_CAUSE_SELECTOR_HOLDOUT_COLLECTION_MANIFEST_REPORT),
                    selector_holdout_priority_collection_capture_audit["source"],
                    selector_holdout_priority_collection_capture_audit["report"],
                    selector_holdout_priority_capture_miss["source"],
                    selector_holdout_priority_capture_miss["report"],
                    selector_holdout_blocker_status["source"],
                    selector_holdout_blocker_status["report"],
                    worker_negative_column_roi_blocker["source"],
                    worker_negative_column_roi_blocker["report"],
                    selector_context_trajectory_protocol["source"],
                    selector_context_trajectory_protocol["report"],
                    selector_holdout_context_worklist["source"],
                    selector_holdout_context_worklist["report"],
                    selector_holdout_context_action_plan["source"],
                    selector_holdout_context_action_plan["report"],
                    str(OBJECTIVE_COMPLETION_AUDIT_SUMMARY),
                    str(OBJECTIVE_COMPLETION_AUDIT_REPORT),
                    str(NEXT_EVIDENCE_PROTOCOL_CATALOG_SUMMARY),
                    str(NEXT_EVIDENCE_PROTOCOL_CATALOG_REPORT),
                    str(EVIDENCE_BUNDLE_MANIFEST_SUMMARY),
                    str(EVIDENCE_BUNDLE_MANIFEST_REPORT),
                    str(EVIDENCE_BUNDLE_REBUILD_SCRIPT),
                    str(EVIDENCE_BUNDLE_REBUILD_SUMMARY),
                    str(EVIDENCE_BUNDLE_REBUILD_REPORT),
                    production_ab_entry_gate_catalog["source"],
                    production_ab_entry_gate_catalog["report"],
                    optimization_direction_candidate_registry["source"],
                    optimization_direction_candidate_registry["report"],
                    failure_matrix["source"],
                    failure_matrix["report"],
                ],
                "key_metrics": {
                    "goal_complete": goal_audit["goal_complete"],
                    "production_direction_proven": completion_requirements[
                        "production_direction_proven"
                    ],
                    "missing_requirement_names": [
                        item["requirement"] for item in missing_requirements
                    ],
                    "failure_matrix_route_count": failure_matrix["route_count"],
                    "failure_matrix_missing_route_ids": (
                        failure_matrix["missing_route_ids"]
                    ),
                    "failure_matrix_statuses": failure_matrix["route_statuses"],
                    "approved_production_direction_count": (
                        optimization_direction_candidate_registry[
                            "approved_production_direction_count"
                        ]
                    ),
                    "current_allowed_next_stage": (
                        optimization_direction_candidate_registry[
                            "current_allowed_next_stage"
                        ]
                    ),
                    "next_action_status": checks["root_cause_next_action_plan"][
                        "status"
                    ],
                    "next_action_immediate_action_ids": checks[
                        "root_cause_next_action_plan"
                    ]["immediate_action_ids"],
                    "selector_collection_status": checks[
                        "root_cause_selector_collection_plan"
                    ]["status"],
                    "selector_collection_target_ids": checks[
                        "root_cause_selector_collection_plan"
                    ]["target_ids"],
                    "selector_collection_schema_row_count": (
                        selector_collection_schema_coverage["row_count"]
                    ),
                    "selector_collection_schema_journey_missing_count": (
                        selector_collection_schema_coverage[
                            "journey_missing_count"
                        ]
                    ),
                    "selector_holdout_collection_target_count": (
                        selector_holdout_collection_manifest[
                            "collection_target_count"
                        ]
                    ),
                    "selector_holdout_targets_needing_active_basis_snapshot_count": (
                        selector_holdout_collection_manifest[
                            "targets_needing_active_basis_snapshot_count"
                        ]
                    ),
                },
            },
        ],
    }
    ruled_out_hypotheses = {
        "schema_version": "root_cause_ruled_out_hypotheses_v1",
        "entries": [
            {
                "hypothesis_id": "pulse_wiring_or_certificate_semantics_is_the_main_cause",
                "status": "ruled_out_as_primary_root_cause",
                "reason": (
                    "Worker/capture paths can add or record true-RC negative "
                    "journeys without critical disagreement, but this does not "
                    "produce stable 20-task ROI."
                ),
                "evidence": {
                    "critical_disagreement_count_phase7o": checks[
                        "phase7o_worker_roi"
                    ]["critical_disagreement_count"],
                    "critical_disagreement_count_phase8q": checks[
                        "phase8q_worker_add_columns"
                    ]["critical_disagreement_count"],
                    "phase8q_added_journeys": checks[
                        "phase8q_worker_add_columns"
                    ]["pulse_worker_added_journeys"],
                    "phase8q_all_time_limit": checks[
                        "phase8q_worker_add_columns"
                    ]["all_time_limit"],
                },
            },
            {
                "hypothesis_id": "finding_more_true_rc_negative_columns_is_sufficient",
                "status": "ruled_out",
                "reason": (
                    "Phase 8Q added true-RC negative journeys, including new "
                    "task sets, while all rows still ended in TIME_LIMIT."
                ),
                "evidence": {
                    "added_journeys": checks["phase8q_worker_add_columns"][
                        "pulse_worker_added_journeys"
                    ],
                    "added_new_task_set_count": checks[
                        "phase8q_worker_add_columns"
                    ]["pulse_worker_added_new_task_set_count"],
                    "added_support_changing_count": checks[
                        "phase8q_worker_add_columns"
                    ]["pulse_worker_added_support_changing_count"],
                    "all_time_limit": checks["phase8q_worker_add_columns"][
                        "all_time_limit"
                    ],
                    "worker_negative_roi_blocker_status": (
                        worker_negative_column_roi_blocker["status"]
                    ),
                    "phase7o_added_journeys": (
                        worker_negative_column_roi_blocker[
                            "phase7o_worker_added_journeys"
                        ]
                    ),
                    "phase7o_added_new_task_sets": (
                        worker_negative_column_roi_blocker[
                            "phase7o_worker_added_new_task_sets"
                        ]
                    ),
                    "phase7o_nonbaseline_worsened_rows": (
                        worker_negative_column_roi_blocker[
                            "phase7o_nonbaseline_worsened_rows"
                        ]
                    ),
                    "phase7o_nonbaseline_rows": (
                        worker_negative_column_roi_blocker[
                            "phase7o_nonbaseline_rows"
                        ]
                    ),
                },
            },
            {
                "hypothesis_id": "expanding_worker_budget_or_default_worker_is_safe_for_5_10",
                "status": "ruled_out",
                "reason": (
                    "Small-scale triggered mechanisms consistently worsen wall "
                    "time, while non-triggered rows preserve official results."
                ),
                "evidence": {
                    "triggered_rows": checks["small_scale_overhead"][
                        "triggered_rows"
                    ],
                    "triggered_worse_count": checks["small_scale_overhead"][
                        "triggered_worse_count"
                    ],
                    "triggered_better_count": checks["small_scale_overhead"][
                        "triggered_better_count"
                    ],
                    "nontriggered_official_changed": checks[
                        "small_scale_overhead"
                    ]["nontriggered_official_changed"],
                    "task10_triggered": checks["current_small_summary_scan"][
                        "task10_triggered"
                    ],
                },
            },
            {
                "hypothesis_id": "true_rc_threshold_or_simple_selector_is_production_ready",
                "status": "ruled_out",
                "reason": (
                    "Replay-local selector candidates exist, but broad "
                    "dataset/instance holdout pass counts are zero and exact "
                    "candidate audit still has false positives and false negatives."
                ),
                "evidence": {
                    "recommended_selector_candidate": checks[
                        "replay_calibrated_selector_candidate"
                    ]["recommended_selector_candidate"],
                    "exact_false_positive_count": selector_holdout[
                        "exact_false_positive_count"
                    ],
                    "exact_false_negative_count": selector_holdout[
                        "exact_false_negative_count"
                    ],
                    "broad_dataset_holdout_pass_count": selector_holdout[
                        "broad_dataset_holdout_pass_count"
                    ],
                    "broad_instance_holdout_pass_count": selector_holdout[
                        "broad_instance_holdout_pass_count"
                    ],
                    "false_positive_new_task_set_noop_count": (
                        selector_error_anatomy[
                            "false_positive_new_task_set_noop_count"
                        ]
                    ),
                    "false_negative_new_task_set_improved_count": (
                        selector_error_anatomy[
                            "false_negative_new_task_set_improved_count"
                        ]
                    ),
                    "perfect_true_rc_threshold_count": (
                        selector_threshold_frontier["perfect_threshold_count"]
                    ),
                    "zero_false_positive_best_recall": (
                        selector_threshold_frontier["zero_fp_recall"]
                    ),
                    "zero_false_negative_false_positive_count": (
                        selector_threshold_frontier["zero_fn_fp"]
                    ),
                    "task_set_mixed_group_count": (
                        selector_context_collision["task_set_mixed_group_count"]
                    ),
                    "task_sequence_mixed_group_count": (
                        selector_context_collision[
                            "task_sequence_mixed_group_count"
                        ]
                    ),
                    "online_flags_mixed_row_count": (
                        selector_context_collision["online_flags_mixed_row_count"]
                    ),
                    "task_set_true_rc_improved_lower_count": (
                        selector_local_feature_direction[
                            "task_set_true_rc_improved_lower_count"
                        ]
                    ),
                    "task_set_true_rc_noop_lower_count": (
                        selector_local_feature_direction[
                            "task_set_true_rc_noop_lower_count"
                        ]
                    ),
                    "task_sequence_true_rc_improved_lower_count": (
                        selector_local_feature_direction[
                            "task_sequence_true_rc_improved_lower_count"
                        ]
                    ),
                    "task_sequence_true_rc_noop_lower_count": (
                        selector_local_feature_direction[
                            "task_sequence_true_rc_noop_lower_count"
                        ]
                    ),
                    "candidate_selector_models_strict_gate_passing": checks[
                        "candidate_selector_models"
                    ]["leave_one_dataset"]["strict_selector_gate"]["passing_models"],
                },
            },
            {
                "hypothesis_id": "hindsight_or_post_addition_signals_can_be_used_online",
                "status": "forbidden_shortcut",
                "reason": (
                    "Hindsight trajectory signals are stronger but are not "
                    "addition-before features and cannot be used for an online "
                    "exact-safe selector."
                ),
                "evidence": {
                    "pre_batch_lod_precision": checks[
                        "trajectory_signal_ladder"
                    ]["layer_summary"]["pre_batch"]["leave_one_dataset"][
                        "precision"
                    ],
                    "immediate_addition_lod_precision": checks[
                        "trajectory_signal_ladder"
                    ]["layer_summary"]["immediate_addition"][
                        "leave_one_dataset"
                    ]["precision"],
                    "hindsight_lod_precision": checks[
                        "trajectory_signal_ladder"
                    ]["layer_summary"]["hindsight_trajectory"][
                        "leave_one_dataset"
                    ]["precision"],
                    "selector_feature_scope": "addition_before_only",
                },
            },
        ],
    }
    why_many_attempts_failed = {
        "schema_version": "root_cause_why_many_attempts_failed_v1",
        "status": "supported_but_optimization_direction_unproven",
        "primary_causes": [
            {
                "cause_id": "small_scale_fixed_overhead_sensitivity",
                "summary": (
                    "5/10 runs are short enough that any triggered worker/audit/"
                    "probe overhead can dominate useful pricing work."
                ),
                "evidence_conclusion_id": "small_scale_fixed_overhead_sensitivity",
                "key_metrics": {
                    "triggered_worse_count": checks["small_scale_overhead"][
                        "triggered_worse_count"
                    ],
                    "triggered_better_count": checks["small_scale_overhead"][
                        "triggered_better_count"
                    ],
                    "task10_triggered_official_changed": checks[
                        "current_small_summary_scan"
                    ]["task10_triggered"]["official_changed"],
                },
            },
            {
                "cause_id": "twenty_returned_batch_rmp_trajectory_coupling",
                "summary": (
                    "20-task runs can receive true-RC negative columns, but "
                    "downstream benefit depends on returned-batch composition "
                    "and current RMP active-basis trajectory."
                ),
                "evidence_conclusion_id": (
                    "true_rc_negative_can_be_high_impact_or_noop"
                ),
                "key_metrics": {
                    "phase8q_added_journeys": checks[
                        "phase8q_worker_add_columns"
                    ]["pulse_worker_added_journeys"],
                    "phase8q_all_time_limit": checks[
                        "phase8q_worker_add_columns"
                    ]["all_time_limit"],
                    "replay_high_impact_candidate_count": replay_real_capture[
                        "high_impact_candidate_count"
                    ],
                    "replay_noop_candidate_count": replay_duplicate_noop[
                        "noop_candidate_count"
                    ],
                    "active_basis_counterexample_task20_row_count": (
                        active_basis_snapshot_counterexamples["task20_row_count"]
                    ),
                    "active_basis_counterexample_task20_new_task_set_count": (
                        active_basis_snapshot_counterexamples[
                            "task20_new_task_set_row_count"
                        ]
                    ),
                    "active_basis_counterexample_task20_label_counts": (
                        active_basis_snapshot_counterexamples["task20_label_counts"]
                    ),
                    "active_basis_counterexample_strongest_noop_true_reduced_cost": (
                        active_basis_snapshot_counterexamples[
                            "strongest_noop_true_reduced_cost"
                        ]
                    ),
                    "active_basis_counterexample_weaker_improved_than_strongest_noop_count": (
                        active_basis_snapshot_counterexamples[
                            "weaker_improved_than_strongest_noop_count"
                        ]
                    ),
                    "worker_negative_roi_blocker_status": (
                        worker_negative_column_roi_blocker["status"]
                    ),
                    "phase7o_worker_added_journeys": (
                        worker_negative_column_roi_blocker[
                            "phase7o_worker_added_journeys"
                        ]
                    ),
                    "phase7o_worker_added_new_task_sets": (
                        worker_negative_column_roi_blocker[
                            "phase7o_worker_added_new_task_sets"
                        ]
                    ),
                    "phase7o_nonbaseline_worsened_rows": (
                        worker_negative_column_roi_blocker[
                            "phase7o_nonbaseline_worsened_rows"
                        ]
                    ),
                    "phase7o_nonbaseline_rows": (
                        worker_negative_column_roi_blocker[
                            "phase7o_nonbaseline_rows"
                        ]
                    ),
                    "phase8q_worker_added_journeys": (
                        worker_negative_column_roi_blocker[
                            "phase8q_worker_added_journeys"
                        ]
                    ),
                    "phase8q_worker_added_rows": (
                        worker_negative_column_roi_blocker[
                            "phase8q_worker_added_rows"
                        ]
                    ),
                    "phase8q_improved_without_worker_added_count": (
                        worker_negative_column_roi_blocker[
                            "phase8q_improved_without_worker_added_count"
                        ]
                    ),
                },
            },
            {
                "cause_id": "addition_before_selector_not_production_validated",
                "summary": (
                    "Current replay-calibrated selector signals do not pass "
                    "context/instance/dataset holdouts, so they cannot be used "
                    "as a production gate before full BPC A/B."
                ),
                "evidence_conclusion_id": "selector_not_production_validated",
                "key_metrics": {
                    "recommended_selector_candidate": checks[
                        "replay_calibrated_selector_candidate"
                    ]["recommended_selector_candidate"],
                    "exact_false_positive_count": selector_holdout[
                        "exact_false_positive_count"
                    ],
                    "exact_false_negative_count": selector_holdout[
                        "exact_false_negative_count"
                    ],
                    "robust_all_fold_selector_available": (
                        completion_requirements["has_robust_all_fold_selector"]
                    ),
                    "production_validated_selector": (
                        completion_requirements["has_production_validated_selector"]
                    ),
                    "active_basis_counterexample_false_positive_count": (
                        active_basis_snapshot_counterexamples["false_positive_count"]
                    ),
                    "active_basis_counterexample_positive_churn_label_counts": (
                        active_basis_snapshot_counterexamples[
                            "positive_churn_label_counts"
                        ]
                    ),
                    "active_basis_counterexample_degeneracy_one_label_counts": (
                        active_basis_snapshot_counterexamples[
                            "degeneracy_one_label_counts"
                        ]
                    ),
                    "active_basis_counterexample_mixed_instance_group_count": (
                        active_basis_snapshot_counterexamples[
                            "mixed_instance_group_count"
                        ]
                    ),
                    "component_payload_rows_candidate_row_count": (
                        component_payload_addition_before_rows["candidate_row_count"]
                    ),
                    "component_payload_rows_explicit_forbidden_true_count": (
                        component_payload_addition_before_rows[
                            "explicit_forbidden_true_count"
                        ]
                    ),
                    "component_payload_rows_runs_local_rmp_replay": (
                        component_payload_addition_before_rows[
                            "runs_local_rmp_replay"
                        ]
                    ),
                    "component_payload_selector_extension_combined_row_count": (
                        component_payload_selector_holdout_extension[
                            "combined_row_count"
                        ]
                    ),
                    "component_payload_selector_extension_component_positive_only": (
                        component_payload_selector_holdout_extension[
                            "component_positive_only"
                        ]
                    ),
                    "component_payload_selector_extension_combined_robust_feature_count": (
                        component_payload_selector_holdout_extension[
                            "combined_robust_all_holdout_derived_feature_count"
                        ]
                    ),
                    "component_payload_selector_extension_combined_robust_model_count": (
                        component_payload_selector_holdout_extension[
                            "combined_robust_all_holdout_model_count"
                        ]
                    ),
                    "priority_collection_capture_event_count": (
                        selector_holdout_priority_collection_capture_audit[
                            "capture_event_count"
                        ]
                    ),
                    "priority_collection_expected_context_hash_count": (
                        selector_holdout_priority_collection_capture_audit[
                            "expected_context_hash_count"
                        ]
                    ),
                    "priority_collection_expected_context_hit_count": (
                        selector_holdout_priority_collection_capture_audit[
                            "expected_context_hit_count"
                        ]
                    ),
                    "priority_collection_ready_for_selector_holdout": (
                        selector_holdout_priority_collection_capture_audit[
                            "ready_for_selector_holdout"
                        ]
                    ),
                    "priority_capture_miss_source_active_hash_missing_context_count": (
                        selector_holdout_priority_capture_miss[
                            "source_active_hash_missing_context_count"
                        ]
                    ),
                    "priority_capture_miss_same_active_component_drift_context_count": (
                        selector_holdout_priority_capture_miss[
                            "same_active_component_drift_context_count"
                        ]
                    ),
                    "context_trajectory_protocol_exact_context_component_count": (
                        selector_context_trajectory_protocol[
                            "exact_context_component_count"
                        ]
                    ),
                    "context_trajectory_protocol_required_capture_payload_count": (
                        selector_context_trajectory_protocol[
                            "required_capture_payload_count"
                        ]
                    ),
                    "source_profile_rerun_is_not_sufficient": (
                        selector_context_trajectory_protocol[
                            "source_profile_rerun_is_not_sufficient"
                        ]
                    ),
                    "same_active_hash_is_not_sufficient": (
                        selector_context_trajectory_protocol[
                            "same_active_hash_is_not_sufficient"
                        ]
                    ),
                    "selector_holdout_context_worklist_unresolved_context_count": (
                        selector_holdout_context_worklist[
                            "unresolved_context_count"
                        ]
                    ),
                    "selector_holdout_context_worklist_actionable_context_count": (
                        selector_holdout_context_worklist[
                            "actionable_context_count"
                        ]
                    ),
                    "selector_holdout_context_worklist_priority_miss_class_counts": (
                        selector_holdout_context_worklist[
                            "priority_miss_class_counts"
                        ]
                    ),
                    "selector_holdout_context_action_unresolved_action_count": (
                        selector_holdout_context_action_plan[
                            "unresolved_action_count"
                        ]
                    ),
                    "selector_holdout_context_action_unresolved_with_command_count": (
                        selector_holdout_context_action_plan[
                            "unresolved_with_command_count"
                        ]
                    ),
                    "selector_holdout_context_action_unresolved_without_command_count": (
                        selector_holdout_context_action_plan[
                            "unresolved_without_command_count"
                        ]
                    ),
                    "selector_holdout_context_action_unresolved_execution_category_counts": (
                        selector_holdout_context_action_plan[
                            "unresolved_execution_category_counts"
                        ]
                    ),
                },
            },
        ],
        "ruled_out_as_sufficient_explanations": [
            {
                "hypothesis_id": entry["hypothesis_id"],
                "status": entry["status"],
                "reason": entry["reason"],
            }
            for entry in ruled_out_hypotheses["entries"]
        ],
        "next_evidence_status": "calibration_only_until_selector_passes",
        "missing_requirements": [
            item["requirement"] for item in missing_requirements
        ],
    }
    expected_evidence_conclusion_ids = {
        "small_scale_fixed_overhead_sensitivity",
        "twenty_negative_columns_not_sufficient",
        "true_rc_negative_can_be_high_impact_or_noop",
        "selector_not_production_validated",
        "exact_context_capture_ready_but_calibration_only",
        "objective_completion_blocked",
    }
    actual_evidence_conclusion_ids = {
        str(entry.get("conclusion_id", ""))
        for entry in evidence_source_index["entries"]
    }
    evidence_primary_artifacts = sorted(
        {
            str(artifact)
            for entry in evidence_source_index["entries"]
            for artifact in entry.get("primary_artifacts", [])
            if artifact
        }
    )
    missing_evidence_primary_artifacts = [
        artifact
        for artifact in evidence_primary_artifacts
        if not Path(artifact).exists()
    ]
    evidence_source_entry_issues: list[dict[str, str]] = []
    allowed_evidence_statuses = {
        "supported",
        "supported_not_production",
        "blocking",
    }
    for entry in evidence_source_index["entries"]:
        conclusion_id = str(entry.get("conclusion_id", ""))
        status = entry.get("status")
        summary = entry.get("summary")
        primary_artifacts = entry.get("primary_artifacts")
        key_metrics = entry.get("key_metrics")
        if not conclusion_id:
            evidence_source_entry_issues.append(
                {"conclusion_id": conclusion_id, "issue": "missing_conclusion_id"}
            )
        if status not in allowed_evidence_statuses:
            evidence_source_entry_issues.append(
                {"conclusion_id": conclusion_id, "issue": "unexpected_status"}
            )
        if not isinstance(summary, str) or not summary.strip():
            evidence_source_entry_issues.append(
                {"conclusion_id": conclusion_id, "issue": "missing_summary"}
            )
        if not isinstance(primary_artifacts, list) or not primary_artifacts:
            evidence_source_entry_issues.append(
                {"conclusion_id": conclusion_id, "issue": "missing_primary_artifacts"}
            )
        if not isinstance(key_metrics, dict) or not key_metrics:
            evidence_source_entry_issues.append(
                {"conclusion_id": conclusion_id, "issue": "missing_key_metrics"}
            )
        elif not _evidence_metric_value_is_populated(key_metrics):
            evidence_source_entry_issues.append(
                {"conclusion_id": conclusion_id, "issue": "empty_key_metric_value"}
            )
    root_cause_document_path_refs = _document_path_reference_audit(
        [
            FINAL_REPORT,
            ROOT_CAUSE_DIAGNOSIS_REPORT,
            OPTIMIZATION_DIRECTION_READINESS_REPORT,
        ]
    )
    expected_ruled_out_hypothesis_ids = {
        "pulse_wiring_or_certificate_semantics_is_the_main_cause",
        "finding_more_true_rc_negative_columns_is_sufficient",
        "expanding_worker_budget_or_default_worker_is_safe_for_5_10",
        "true_rc_threshold_or_simple_selector_is_production_ready",
        "hindsight_or_post_addition_signals_can_be_used_online",
    }
    actual_ruled_out_hypothesis_ids = {
        str(entry.get("hypothesis_id", ""))
        for entry in ruled_out_hypotheses["entries"]
    }
    allowed_ruled_out_statuses = {
        "ruled_out_as_primary_root_cause",
        "ruled_out",
        "forbidden_shortcut",
    }
    ruled_out_hypothesis_issues: list[dict[str, str]] = []
    for entry in ruled_out_hypotheses["entries"]:
        hypothesis_id = str(entry.get("hypothesis_id", ""))
        status = entry.get("status")
        reason = entry.get("reason")
        evidence = entry.get("evidence")
        if not hypothesis_id:
            ruled_out_hypothesis_issues.append(
                {"hypothesis_id": hypothesis_id, "issue": "missing_hypothesis_id"}
            )
        if status not in allowed_ruled_out_statuses:
            ruled_out_hypothesis_issues.append(
                {"hypothesis_id": hypothesis_id, "issue": "unexpected_status"}
            )
        if not isinstance(reason, str) or not reason.strip():
            ruled_out_hypothesis_issues.append(
                {"hypothesis_id": hypothesis_id, "issue": "missing_reason"}
            )
        if not isinstance(evidence, dict) or not evidence:
            ruled_out_hypothesis_issues.append(
                {"hypothesis_id": hypothesis_id, "issue": "missing_evidence"}
            )
        elif not _evidence_metric_value_is_populated(evidence):
            ruled_out_hypothesis_issues.append(
                {"hypothesis_id": hypothesis_id, "issue": "empty_evidence_value"}
            )
    expected_why_primary_cause_ids = [
        "small_scale_fixed_overhead_sensitivity",
        "twenty_returned_batch_rmp_trajectory_coupling",
        "addition_before_selector_not_production_validated",
    ]
    why_primary_cause_ids = [
        str(entry.get("cause_id", ""))
        for entry in why_many_attempts_failed["primary_causes"]
    ]
    why_many_attempts_failed_issues: list[dict[str, str]] = []
    if why_many_attempts_failed["status"] != (
        "supported_but_optimization_direction_unproven"
    ):
        why_many_attempts_failed_issues.append(
            {"scope": "why_many_attempts_failed", "issue": "unexpected_status"}
        )
    if why_primary_cause_ids != expected_why_primary_cause_ids:
        why_many_attempts_failed_issues.append(
            {
                "scope": "why_many_attempts_failed",
                "issue": "primary_cause_id_mismatch",
            }
        )
    if len(why_many_attempts_failed["ruled_out_as_sufficient_explanations"]) != len(
        ruled_out_hypotheses["entries"]
    ):
        why_many_attempts_failed_issues.append(
            {
                "scope": "why_many_attempts_failed",
                "issue": "ruled_out_count_mismatch",
            }
        )
    if why_many_attempts_failed["missing_requirements"] != [
        item["requirement"] for item in missing_requirements
    ]:
        why_many_attempts_failed_issues.append(
            {
                "scope": "why_many_attempts_failed",
                "issue": "missing_requirements_mismatch",
            }
        )
    why_cause_metrics = {
        str(entry.get("cause_id", "")): entry.get("key_metrics", {})
        for entry in why_many_attempts_failed["primary_causes"]
    }
    twenty_why_metrics = why_cause_metrics.get(
        "twenty_returned_batch_rmp_trajectory_coupling", {}
    )
    twenty_why_label_counts = twenty_why_metrics.get(
        "active_basis_counterexample_task20_label_counts", {}
    )
    if not (
        _as_int(twenty_why_metrics.get("active_basis_counterexample_task20_row_count"))
        == 12
        and _as_int(
            twenty_why_metrics.get(
                "active_basis_counterexample_task20_new_task_set_count"
            )
        )
        == 12
        and _as_int(twenty_why_label_counts.get("improved")) == 10
        and _as_int(twenty_why_label_counts.get("noop")) == 2
        and _as_float(
            twenty_why_metrics.get(
                "active_basis_counterexample_strongest_noop_true_reduced_cost"
            )
        )
        == -128.547499
        and _as_int(
            twenty_why_metrics.get(
                "active_basis_counterexample_weaker_improved_than_strongest_noop_count"
            )
        )
        > 0
    ):
        why_many_attempts_failed_issues.append(
            {
                "scope": "why_many_attempts_failed",
                "issue": "active_basis_counterexample_twenty_metrics_missing",
            }
        )
    if not (
        twenty_why_metrics.get("worker_negative_roi_blocker_status")
        == "worker_negative_columns_not_sufficient_for_roi"
        and _as_int(twenty_why_metrics.get("phase7o_worker_added_journeys")) == 63
        and _as_int(twenty_why_metrics.get("phase7o_worker_added_new_task_sets"))
        == 30
        and _as_int(twenty_why_metrics.get("phase7o_nonbaseline_worsened_rows"))
        == 96
        and _as_int(twenty_why_metrics.get("phase7o_nonbaseline_rows")) == 96
        and _as_int(twenty_why_metrics.get("phase8q_worker_added_journeys")) == 10
        and _as_int(twenty_why_metrics.get("phase8q_worker_added_rows")) == 3
        and _as_int(
            twenty_why_metrics.get("phase8q_improved_without_worker_added_count")
        )
        == 1
    ):
        why_many_attempts_failed_issues.append(
            {
                "scope": "why_many_attempts_failed",
                "issue": "worker_negative_roi_blocker_metrics_missing",
            }
        )
    selector_why_metrics = why_cause_metrics.get(
        "addition_before_selector_not_production_validated", {}
    )
    positive_churn_labels = selector_why_metrics.get(
        "active_basis_counterexample_positive_churn_label_counts", {}
    )
    degeneracy_one_labels = selector_why_metrics.get(
        "active_basis_counterexample_degeneracy_one_label_counts", {}
    )
    if not (
        _as_int(
            selector_why_metrics.get(
                "active_basis_counterexample_false_positive_count"
            )
        )
        >= 2
        and _as_int(positive_churn_labels.get("improved")) > 0
        and _as_int(positive_churn_labels.get("noop")) > 0
        and _as_int(degeneracy_one_labels.get("improved")) > 0
        and _as_int(degeneracy_one_labels.get("noop")) > 0
            and _as_int(
                selector_why_metrics.get(
                    "active_basis_counterexample_mixed_instance_group_count"
                )
            )
            > 0
            and _as_int(
                selector_why_metrics.get("component_payload_rows_candidate_row_count")
            )
            == 48
            and _as_int(
                selector_why_metrics.get(
                    "component_payload_rows_explicit_forbidden_true_count"
                )
            )
            == 48
            and selector_why_metrics.get("component_payload_rows_runs_local_rmp_replay")
            is True
            and _as_int(
                selector_why_metrics.get(
                    "component_payload_selector_extension_combined_row_count"
                )
            )
            == 328
            and selector_why_metrics.get(
                "component_payload_selector_extension_component_positive_only"
            )
            is True
            and _as_int(
                selector_why_metrics.get(
                    "component_payload_selector_extension_combined_robust_feature_count"
                )
            )
            == 0
            and _as_int(
                selector_why_metrics.get(
                    "component_payload_selector_extension_combined_robust_model_count"
                )
            )
            == 0
            and _as_int(
                selector_why_metrics.get(
                    "context_trajectory_protocol_exact_context_component_count"
                )
            )
            == 9
            and _as_int(
                selector_why_metrics.get(
                    "context_trajectory_protocol_required_capture_payload_count"
                )
            )
            == 9
            and selector_why_metrics.get("source_profile_rerun_is_not_sufficient")
            is True
            and selector_why_metrics.get("same_active_hash_is_not_sufficient")
            is True
        ):
            why_many_attempts_failed_issues.append(
                {
                "scope": "why_many_attempts_failed",
                "issue": "active_basis_counterexample_selector_metrics_missing",
            }
        )
    expected_missing_requirement_names = [
        "five_ten_full_no_regression_ab",
        "production_validated_selector",
        "twenty_walltime_speedup",
    ]
    missing_requirement_names = [
        str(item.get("requirement", "")) for item in missing_requirements
    ]
    missing_requirement_entry_issues: list[dict[str, str]] = []
    for item in missing_requirements:
        requirement = str(item.get("requirement", ""))
        if requirement not in expected_missing_requirement_names:
            missing_requirement_entry_issues.append(
                {"requirement": requirement, "issue": "unexpected_requirement"}
            )
        for field in ("reason", "required_next_evidence"):
            value = item.get(field)
            if not isinstance(value, str) or not value.strip():
                missing_requirement_entry_issues.append(
                    {"requirement": requirement, "issue": f"missing_{field}"}
                )
        evidence = item.get("evidence")
        if not isinstance(evidence, dict) or not evidence:
            missing_requirement_entry_issues.append(
                {"requirement": requirement, "issue": "missing_evidence"}
            )
    expected_objective_audit_requirements = [
        "root_cause_explanation_has_evidence",
        "not_limited_to_pulse",
        "no_unvalidated_mainline_change_before_proof",
        "unproven_experiments_not_counted_as_completion",
        "five_ten_no_regression_is_noop_guard_not_worker_success",
        "stable_production_optimization_direction",
        "exact_5_10_no_regression_and_20_speedup",
    ]
    expected_not_proved_audit_requirements = {
        "stable_production_optimization_direction",
        "exact_5_10_no_regression_and_20_speedup",
    }
    objective_audit_items = list(objective_requirement_audit.get("audit_items", []))
    objective_audit_requirement_names = [
        str(item.get("requirement", "")) for item in objective_audit_items
    ]
    objective_audit_not_proved_requirements = {
        str(item.get("requirement", ""))
        for item in objective_audit_items
        if item.get("status") == "not_proved"
    }
    objective_audit_item_issues: list[dict[str, str]] = []
    for item in objective_audit_items:
        requirement = str(item.get("requirement", ""))
        status = item.get("status")
        evidence = item.get("evidence")
        if requirement not in expected_objective_audit_requirements:
            objective_audit_item_issues.append(
                {"requirement": requirement, "issue": "unexpected_requirement"}
            )
        if status not in {"proved", "not_proved"}:
            objective_audit_item_issues.append(
                {"requirement": requirement, "issue": "unexpected_status"}
            )
        if not _evidence_metric_value_is_populated(evidence):
            objective_audit_item_issues.append(
                {"requirement": requirement, "issue": "missing_or_empty_evidence"}
            )
    expected_next_evidence_gates = [
        "exact_context_capture_and_replay_dataset",
        "addition_before_selector",
        "production_candidate_ab",
    ]
    expected_selector_holdouts = ("context", "instance", "dataset")
    expected_forbidden_shortcuts = {
        "post_addition_or_hindsight_features",
        "single_context_replay_success",
        "worker_negative_columns_without_walltime_roi",
        "certificate_effect",
    }
    next_evidence_protocol = list(readiness["next_evidence_protocol"])
    next_evidence_protocol_readiness = list(
        readiness["next_evidence_protocol_readiness"]
    )
    next_evidence_protocol_issues: list[dict[str, str]] = []
    if next_evidence_gates.get("calibration_only_until_selector_passes") is not True:
        next_evidence_protocol_issues.append(
            {"gate": "global", "issue": "calibration_only_gate_not_true"}
        )
    if next_evidence_gates.get("selector_feature_scope") != "addition_before_only":
        next_evidence_protocol_issues.append(
            {"gate": "global", "issue": "selector_feature_scope_not_addition_before"}
        )
    if tuple(next_evidence_gates.get("required_selector_holdouts", ())) != (
        expected_selector_holdouts
    ):
        next_evidence_protocol_issues.append(
            {"gate": "global", "issue": "selector_holdouts_do_not_match_expected"}
        )
    if (
        next_evidence_gates.get("require_5_10_no_regression_gate_before_production")
        is not True
    ):
        next_evidence_protocol_issues.append(
            {"gate": "global", "issue": "missing_5_10_production_gate"}
        )
    if (
        next_evidence_gates.get("require_selected_20_hard_repeat_ab_before_production")
        is not True
    ):
        next_evidence_protocol_issues.append(
            {"gate": "global", "issue": "missing_selected_20_ab_gate"}
        )
    if set(next_evidence_gates.get("forbidden_shortcuts", ())) != (
        expected_forbidden_shortcuts
    ):
        next_evidence_protocol_issues.append(
            {"gate": "global", "issue": "forbidden_shortcuts_do_not_match_expected"}
        )
    protocol_gate_names = [
        str(item.get("gate", "")) for item in next_evidence_protocol
    ]
    readiness_gate_names = [
        str(item.get("gate", "")) for item in next_evidence_protocol_readiness
    ]
    if protocol_gate_names != expected_next_evidence_gates:
        next_evidence_protocol_issues.append(
            {"gate": "protocol", "issue": "protocol_gates_do_not_match_expected"}
        )
    if readiness_gate_names != expected_next_evidence_gates:
        next_evidence_protocol_issues.append(
            {"gate": "readiness", "issue": "readiness_gates_do_not_match_expected"}
        )
    for item in next_evidence_protocol:
        gate = str(item.get("gate", ""))
        for field in ("purpose", "pass_condition"):
            value = item.get(field)
            if not isinstance(value, str) or not value.strip():
                next_evidence_protocol_issues.append(
                    {"gate": gate, "issue": f"missing_{field}"}
                )
        if not item.get("required_artifacts"):
            next_evidence_protocol_issues.append(
                {"gate": gate, "issue": "missing_required_artifacts"}
            )
        if not item.get("forbidden_shortcuts"):
            next_evidence_protocol_issues.append(
                {"gate": gate, "issue": "missing_forbidden_shortcuts"}
            )
    expected_readiness_passed = {
        "exact_context_capture_and_replay_dataset": True,
        "addition_before_selector": True,
        "production_candidate_ab": False,
    }
    for item in next_evidence_protocol_readiness:
        gate = str(item.get("gate", ""))
        if item.get("passed_for_current_stage") is not expected_readiness_passed.get(
            gate
        ):
            next_evidence_protocol_issues.append(
                {"gate": gate, "issue": "unexpected_readiness_pass_state"}
            )
        evidence = item.get("evidence")
        if not isinstance(evidence, dict) or not evidence:
            next_evidence_protocol_issues.append(
                {"gate": gate, "issue": "missing_or_empty_readiness_evidence"}
            )
    code_boundary_issues: list[dict[str, str]] = []
    code_boundary = checks["root_cause_code_boundary"]
    if not code_boundary["check_code_boundary_no_unvalidated_production_effect"]:
        code_boundary_issues.append(
            {"scope": "root_cause_code_boundary", "issue": "boundary_check_failed"}
        )
    if code_boundary["counterfactual_capture_default_enabled"] is not False:
        code_boundary_issues.append(
            {"scope": "root_cause_code_boundary", "issue": "capture_default_enabled"}
        )
    if code_boundary["counterfactual_capture_certificate_capable"] is not False:
        code_boundary_issues.append(
            {
                "scope": "root_cause_code_boundary",
                "issue": "capture_certificate_capable",
            }
        )
    if code_boundary["counterfactual_capture_official_bound_effect"] is not False:
        code_boundary_issues.append(
            {
                "scope": "root_cause_code_boundary",
                "issue": "capture_official_bound_effect",
            }
        )
    if code_boundary["mainline_unvalidated_effect_default_enabled"] is not False:
        code_boundary_issues.append(
            {
                "scope": "root_cause_code_boundary",
                "issue": "unvalidated_default_effect_enabled",
            }
        )
    ledger_self_consistency_issues: list[dict[str, str]] = []
    if goal_audit["goal_complete"] is not False:
        ledger_self_consistency_issues.append(
            {"scope": "goal_status", "issue": "goal_complete_not_false"}
        )
    if goal_audit["should_mark_goal_complete"] is not False:
        ledger_self_consistency_issues.append(
            {"scope": "goal_status", "issue": "should_mark_goal_complete_not_false"}
        )
    if objective_requirement_audit["decision"] != "keep_goal_active":
        ledger_self_consistency_issues.append(
            {"scope": "completion_decision", "issue": "decision_not_keep_active"}
        )
    if objective_requirement_audit["blocking_missing_requirements"] != missing_requirements:
        ledger_self_consistency_issues.append(
            {"scope": "objective_requirement_audit", "issue": "missing_list_mismatch"}
        )
    if (
        objective_requirement_audit["stable_production_optimization_direction"]
        != completion_requirements["production_direction_proven"]
    ):
        ledger_self_consistency_issues.append(
            {
                "scope": "objective_requirement_audit",
                "issue": "production_direction_flag_mismatch",
            }
        )
    exact_5_10_20_flag = bool(
        completion_requirements["has_small_no_regression_guard"]
        and completion_requirements["has_task5_noop_no_regression_guard"]
        and completion_requirements["has_task10_noop_no_regression_guard"]
        and completion_requirements["has_full_5_10_production_ab_evidence"]
        and completion_requirements["has_20_walltime_speedup_evidence"]
        and completion_requirements["production_direction_proven"]
    )
    if (
        objective_requirement_audit["exact_5_10_no_regression_and_20_speedup"]
        != exact_5_10_20_flag
    ):
        ledger_self_consistency_issues.append(
            {
                "scope": "objective_requirement_audit",
                "issue": "exact_5_10_20_flag_mismatch",
            }
        )
    final_interpretation = (
        "Evidence supports the current root-cause conclusion: small scales are "
        "overhead-sensitive; 20-task runs have negative columns; target002/priority "
        "capture shows exact target contexts are not reliably recovered under current "
        "config-matched reruns because trajectory and pool/forbidden/returned-batch "
        "components drift; and the expanded replay dataset exposes calibrated "
        "addition-before selector candidates. This is still not an optimization "
        "success certificate because no production BPC A/B has proven 5/10 "
        "no-regression plus selected 20-task speedup."
    )
    evidence_integrity_checks = {
        "schema_version": "root_cause_evidence_integrity_checks_v1",
        "ledger_interpretation_no_stale_target002_exact_covered": (
            "target002 is now exact-covered" not in final_interpretation
            and "target002 is exact-covered" not in final_interpretation
        ),
        "evidence_source_index_has_expected_entries": (
            actual_evidence_conclusion_ids == expected_evidence_conclusion_ids
        ),
        "ruled_out_hypotheses_has_expected_entries": (
            actual_ruled_out_hypothesis_ids == expected_ruled_out_hypothesis_ids
        ),
        "ruled_out_hypothesis_issues": ruled_out_hypothesis_issues,
        "ruled_out_hypotheses_structurally_complete": (
            not ruled_out_hypothesis_issues
        ),
        "why_many_attempts_failed_primary_cause_ids": why_primary_cause_ids,
        "why_many_attempts_failed_issues": why_many_attempts_failed_issues,
        "why_many_attempts_failed_structurally_complete": (
            not why_many_attempts_failed_issues
        ),
        "evidence_source_index_has_blocking_entries": any(
            entry.get("status") == "blocking"
            for entry in evidence_source_index["entries"]
        ),
        "evidence_source_index_primary_artifact_count": len(
            evidence_primary_artifacts
        ),
        "evidence_source_index_missing_primary_artifacts": (
            missing_evidence_primary_artifacts
        ),
        "evidence_source_index_primary_artifacts_all_exist": (
            not missing_evidence_primary_artifacts
        ),
        "evidence_source_index_entry_issues": evidence_source_entry_issues,
        "evidence_source_index_entries_structurally_complete": (
            not evidence_source_entry_issues
        ),
        "root_cause_document_path_reference_count": (
            root_cause_document_path_refs["reference_count"]
        ),
        "root_cause_document_missing_path_references": (
            root_cause_document_path_refs["missing_references"]
        ),
        "root_cause_document_path_references_all_exist": (
            root_cause_document_path_refs["all_references_exist"]
        ),
        "missing_requirement_names": missing_requirement_names,
        "missing_requirement_names_match_expected": (
            missing_requirement_names == expected_missing_requirement_names
        ),
        "missing_requirement_entry_issues": missing_requirement_entry_issues,
        "missing_requirements_structurally_complete": (
            not missing_requirement_entry_issues
        ),
        "objective_audit_requirement_names": objective_audit_requirement_names,
        "objective_audit_requirement_names_match_expected": (
            objective_audit_requirement_names == expected_objective_audit_requirements
        ),
        "objective_audit_not_proved_requirements": sorted(
            objective_audit_not_proved_requirements
        ),
        "objective_audit_not_proved_requirements_match_expected": (
            objective_audit_not_proved_requirements
            == expected_not_proved_audit_requirements
        ),
        "objective_audit_item_issues": objective_audit_item_issues,
        "objective_audit_items_structurally_complete": (
            not objective_audit_item_issues
        ),
        "next_evidence_protocol_gate_names": protocol_gate_names,
        "next_evidence_protocol_readiness_gate_names": readiness_gate_names,
        "next_evidence_protocol_issues": next_evidence_protocol_issues,
        "next_evidence_protocol_structurally_complete": (
            not next_evidence_protocol_issues
        ),
        "code_boundary_issues": code_boundary_issues,
        "code_boundary_no_unvalidated_production_effect": (
            not code_boundary_issues
        ),
        "ledger_self_consistency_issues": ledger_self_consistency_issues,
        "ledger_self_consistency_pass": not ledger_self_consistency_issues,
        "ruled_out_hypotheses_all_have_evidence": all(
            bool(entry.get("evidence")) for entry in ruled_out_hypotheses["entries"]
        ),
        "completion_decision_is_keep_active": (
            objective_requirement_audit["decision"] == "keep_goal_active"
        ),
    }
    evidence_integrity_checks["all_integrity_checks_pass"] = all(
        bool(value)
        for key, value in evidence_integrity_checks.items()
        if key
        not in {
            "schema_version",
            "evidence_source_index_primary_artifact_count",
            "evidence_source_index_missing_primary_artifacts",
            "evidence_source_index_entry_issues",
            "root_cause_document_path_reference_count",
            "root_cause_document_missing_path_references",
            "ruled_out_hypothesis_issues",
            "why_many_attempts_failed_primary_cause_ids",
            "why_many_attempts_failed_issues",
            "missing_requirement_names",
            "missing_requirement_entry_issues",
            "objective_audit_requirement_names",
            "objective_audit_not_proved_requirements",
            "objective_audit_item_issues",
            "next_evidence_protocol_gate_names",
            "next_evidence_protocol_readiness_gate_names",
            "next_evidence_protocol_issues",
            "code_boundary_issues",
            "ledger_self_consistency_issues",
        }
    )
    final_all_checks_pass = bool(
        all_checks_pass and evidence_integrity_checks["all_integrity_checks_pass"]
    )
    return {
        "all_checks_pass": final_all_checks_pass,
        "goal_status": {
            "root_cause_explanation_supported": True,
            "goal_complete": goal_audit["goal_complete"],
            "should_mark_goal_complete": goal_audit["should_mark_goal_complete"],
            "production_direction_proven": completion_requirements[
                "production_direction_proven"
            ],
            "has_replay_calibrated_selector_candidate": completion_requirements[
                "has_replay_calibrated_selector_candidate"
            ],
            "has_robust_all_fold_selector": completion_requirements[
                "has_robust_all_fold_selector"
            ],
            "has_robust_all_fold_rule_selector": completion_requirements[
                "has_robust_all_fold_rule_selector"
            ],
            "has_production_validated_selector": completion_requirements[
                "has_production_validated_selector"
            ],
            "has_20_walltime_speedup_evidence": completion_requirements[
                "has_20_walltime_speedup_evidence"
            ],
            "missing_requirement_names": [
                item["requirement"] for item in missing_requirements
            ],
        },
        "evidence_source_index": evidence_source_index,
        "ruled_out_hypotheses": ruled_out_hypotheses,
        "why_many_attempts_failed": why_many_attempts_failed,
        "evidence_integrity_checks": evidence_integrity_checks,
        "objective_requirement_audit": objective_requirement_audit,
        "completion_decision": {
            "status": objective_requirement_audit["decision"],
            "reason": (
                "Root-cause explanation is supported, but these objective "
                "requirements are still missing: "
                + ",".join(item["requirement"] for item in missing_requirements)
                + "."
                if not goal_audit["goal_complete"]
                else "All objective requirements are proved."
            ),
            "missing_requirement_names": [
                item["requirement"] for item in missing_requirements
            ],
        },
        "production_ab_entry_gate": {
            "status": production_ab_entry_gate_catalog["status"],
            "entry_gate_blockers": production_ab_entry_gate_catalog[
                "entry_gate_blockers"
            ],
            "must_not_enable_worker_default": (
                production_ab_entry_gate_catalog[
                    "must_not_enable_worker_default"
                ]
            ),
            "must_not_open_certificate_gate": (
                production_ab_entry_gate_catalog[
                    "must_not_open_certificate_gate"
                ]
            ),
            "requires_selector_holdout_before_ab": (
                production_ab_entry_gate_catalog[
                    "requires_selector_holdout_before_ab"
                ]
            ),
            "selector_feature_scope": production_ab_entry_gate_catalog[
                "selector_feature_scope"
            ],
            "required_selector_holdouts": production_ab_entry_gate_catalog[
                "required_selector_holdouts"
            ],
            "forbidden_shortcuts": production_ab_entry_gate_catalog[
                "forbidden_shortcuts"
            ],
        },
        "completion_requirements": completion_requirements,
        "missing_requirements": missing_requirements,
        "next_evidence_protocol": {
            "schema_version": "root_cause_next_evidence_protocol_v1",
            "status": "calibration_only_until_selector_passes",
            "gates": readiness["next_evidence_protocol"],
            "readiness": readiness["next_evidence_protocol_readiness"],
        },
        "next_required_evidence": {
            "calibration_only_until_selector_passes": next_evidence_gates[
                "calibration_only_until_selector_passes"
            ],
            "selector_feature_scope": next_evidence_gates[
                "selector_feature_scope"
            ],
            "required_selector_holdouts": next_evidence_gates[
                "required_selector_holdouts"
            ],
            "require_5_10_no_regression_gate_before_production": (
                next_evidence_gates[
                    "require_5_10_no_regression_gate_before_production"
                ]
            ),
            "require_selected_20_hard_repeat_ab_before_production": (
                next_evidence_gates[
                    "require_selected_20_hard_repeat_ab_before_production"
                ]
            ),
            "forbidden_shortcuts": next_evidence_gates["forbidden_shortcuts"],
            "protocol": readiness["next_evidence_protocol"],
            "protocol_readiness": readiness["next_evidence_protocol_readiness"],
        },
        "interpretation": final_interpretation,
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()
    ledger = build_evidence_ledger()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "summary.json"
    output_path.write_text(
        json.dumps(ledger, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(ledger, ensure_ascii=False, sort_keys=True))
    return 0 if ledger["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
