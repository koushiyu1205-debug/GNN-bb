"""B5 typed guidance hints and proof-debt shadow accounting."""

from __future__ import annotations

from collections.abc import Iterable as IterableABC
from collections.abc import Mapping as MappingABC
from dataclasses import dataclass
from typing import Iterable, Mapping

from lunar_ice_bpc.exact.bpc.certificates.proof_debt_queue import ProofDebtQueue


REQUIRED_SOLVER_ROI_LABELS: tuple[str, ...] = (
    "observed_true_rc_negative_found_by_final_judge",
    "hidden_negative_miss",
    "harvest_selected_not_selected",
    "candidate_addability_label",
    "delayed_negative_debt_label",
    "active_support_changed",
    "child_proof_cpu",
    "branch_pair_win_loss_same_context",
    "pricing_pressure",
    "certificate_time",
    "no_harvest_cpu",
)

REQUIRED_GUIDANCE_HEADS: tuple[str, ...] = (
    "pricing_priority_head",
    "branch_priority_head",
    "harvest_priority_head",
)

OPTIONAL_GUIDANCE_HEADS: tuple[str, ...] = (
    "proof_tail_risk_head",
    "candidate_addability_head",
    "delayed_negative_debt_head",
    "phase2_pricing_pressure_head",
)


@dataclass(frozen=True)
class GuidanceHint:
    candidate_id: str
    priority: float = 0.0
    source: str = "shadow"
    finite_delay_budget: int = 0
    uncertainty: float = 0.0
    diagnostic_only: bool = True
    model_version: str = "no_model_shadow_v1"
    feature_schema_version: str = "lunar_ice_bpc.guidance_hint.v1"

    def __post_init__(self) -> None:
        if not str(self.candidate_id):
            raise ValueError("candidate_id must be non-empty")
        if int(self.finite_delay_budget) < 0:
            raise ValueError("finite_delay_budget must be non-negative")

    def to_payload(self) -> dict:
        return {
            "candidate_id": str(self.candidate_id),
            "priority": float(self.priority),
            "source": str(self.source),
            "finite_delay_budget": int(self.finite_delay_budget),
            "uncertainty": float(self.uncertainty),
            "diagnostic_only": bool(self.diagnostic_only),
            "model_version": str(self.model_version),
            "feature_schema_version": str(self.feature_schema_version),
        }


def guidance_hint_from_payload(payload: Mapping[str, object]) -> GuidanceHint:
    return GuidanceHint(
        candidate_id=str(payload.get("candidate_id") or payload.get("id") or ""),
        priority=float(payload.get("priority") or 0.0),
        source=str(payload.get("source") or "shadow"),
        finite_delay_budget=int(payload.get("finite_delay_budget") or 0),
        uncertainty=float(payload.get("uncertainty") or 0.0),
        diagnostic_only=bool(payload.get("diagnostic_only", True)),
        model_version=str(payload.get("model_version") or "no_model_shadow_v1"),
        feature_schema_version=str(payload.get("feature_schema_version") or "lunar_ice_bpc.guidance_hint.v1"),
    )


def normalize_guidance_hints(hints: Iterable[GuidanceHint | Mapping[str, object]]) -> tuple[GuidanceHint, ...]:
    normalized = []
    for hint in hints:
        normalized.append(hint if isinstance(hint, GuidanceHint) else guidance_hint_from_payload(hint))
    return tuple(sorted(normalized, key=lambda row: (-float(row.priority), str(row.candidate_id))))


def build_guidance_output_bundle(
    *,
    pricing_priority_head: Iterable[GuidanceHint | Mapping[str, object]] = tuple(),
    branch_priority_head: Iterable[GuidanceHint | Mapping[str, object]] = tuple(),
    harvest_priority_head: Iterable[GuidanceHint | Mapping[str, object]] = tuple(),
    proof_tail_risk_head: Iterable[GuidanceHint | Mapping[str, object]] = tuple(),
    candidate_addability_head: Iterable[GuidanceHint | Mapping[str, object]] = tuple(),
    delayed_negative_debt_head: Iterable[GuidanceHint | Mapping[str, object]] = tuple(),
    phase2_pricing_pressure_head: Iterable[GuidanceHint | Mapping[str, object]] = tuple(),
    ood_diagnostics: Mapping[str, object] | None = None,
    confidence_diagnostics: Mapping[str, object] | None = None,
    diagnostic_policy_versions: Mapping[str, object] | None = None,
) -> dict:
    """Return the typed B5 output-head artifact consumed by exact-safe ordering."""

    head_inputs = {
        "pricing_priority_head": pricing_priority_head,
        "branch_priority_head": branch_priority_head,
        "harvest_priority_head": harvest_priority_head,
        "proof_tail_risk_head": proof_tail_risk_head,
        "candidate_addability_head": candidate_addability_head,
        "delayed_negative_debt_head": delayed_negative_debt_head,
        "phase2_pricing_pressure_head": phase2_pricing_pressure_head,
    }
    heads: dict[str, list[dict]] = {}
    head_counts: dict[str, int] = {}
    model_versions: set[str] = set()
    feature_schema_versions: set[str] = set()
    diagnostic_only_violations: list[str] = []
    for head_name, hints in head_inputs.items():
        normalized = normalize_guidance_hints(hints)
        payloads = [hint.to_payload() for hint in normalized]
        heads[head_name] = payloads
        head_counts[head_name] = len(payloads)
        for hint in normalized:
            model_versions.add(str(hint.model_version))
            feature_schema_versions.add(str(hint.feature_schema_version))
            if not bool(hint.diagnostic_only):
                diagnostic_only_violations.append(f"{head_name}:{hint.candidate_id}")
    required_heads_present = all(head in heads for head in REQUIRED_GUIDANCE_HEADS)
    diagnostic_version_issues = _diagnostic_version_issues(
        ood_diagnostics=ood_diagnostics,
        confidence_diagnostics=confidence_diagnostics,
        diagnostic_policy_versions=diagnostic_policy_versions,
    )
    return {
        "schema_version": "lunar_ice_bpc.b5_guidance_output_bundle.v1",
        "required_heads": list(REQUIRED_GUIDANCE_HEADS),
        "optional_heads": list(OPTIONAL_GUIDANCE_HEADS),
        "heads": heads,
        "head_counts": head_counts,
        "required_heads_present": bool(required_heads_present),
        "non_diagnostic_hint_count": len(diagnostic_only_violations),
        "non_diagnostic_hint_ids": diagnostic_only_violations,
        "model_versions": sorted(model_versions),
        "feature_schema_versions": sorted(feature_schema_versions),
        "ood_diagnostics": dict(ood_diagnostics or {}),
        "confidence_diagnostics": dict(confidence_diagnostics or {}),
        "diagnostic_policy_versions": dict(diagnostic_policy_versions or {}),
        "diagnostic_version_issues": diagnostic_version_issues,
        "diagnostic_versions_complete": not diagnostic_version_issues,
        "ood_confidence_diagnostics_present": bool(ood_diagnostics or confidence_diagnostics),
        "diagnostics_can_certify": False,
        "diagnostics_lower_bound_official": False,
        "guidance_can_construct_certificate": False,
        "guidance_can_mutate_exact_state": False,
        "mutates_solver": False,
        "can_certify": False,
        "can_fathom": False,
        "can_prune": False,
        "exact_status_effect": "none",
        "note": (
            "B5 guidance heads may order candidates and report diagnostics only; "
            "they never create bounds, pruning decisions, or certificate evidence."
        ),
    }


def build_guidance_output_bundle_from_payload(payload: Mapping[str, object] | None) -> dict:
    raw = payload or {}
    heads = raw.get("heads") if isinstance(raw.get("heads"), MappingABC) else {}
    return build_guidance_output_bundle(
        pricing_priority_head=_head_payload(raw, heads, "pricing_priority_head"),
        branch_priority_head=_head_payload(raw, heads, "branch_priority_head"),
        harvest_priority_head=_head_payload(raw, heads, "harvest_priority_head"),
        proof_tail_risk_head=_head_payload(raw, heads, "proof_tail_risk_head"),
        candidate_addability_head=_head_payload(raw, heads, "candidate_addability_head"),
        delayed_negative_debt_head=_head_payload(raw, heads, "delayed_negative_debt_head"),
        phase2_pricing_pressure_head=_head_payload(raw, heads, "phase2_pricing_pressure_head"),
        ood_diagnostics=raw.get("ood_diagnostics") if isinstance(raw.get("ood_diagnostics"), MappingABC) else None,
        confidence_diagnostics=(
            raw.get("confidence_diagnostics")
            if isinstance(raw.get("confidence_diagnostics"), MappingABC)
            else None
        ),
        diagnostic_policy_versions=(
            raw.get("diagnostic_policy_versions")
            if isinstance(raw.get("diagnostic_policy_versions"), MappingABC)
            else None
        ),
    )


def guidance_head_hints(bundle: Mapping[str, object], head_name: str) -> tuple[GuidanceHint, ...]:
    heads = bundle.get("heads") if isinstance(bundle.get("heads"), MappingABC) else {}
    rows = heads.get(str(head_name)) if isinstance(heads, MappingABC) else tuple()
    if not isinstance(rows, IterableABC) or isinstance(rows, (str, bytes)):
        return tuple()
    return normalize_guidance_hints(row for row in rows if isinstance(row, MappingABC))


def all_guidance_bundle_hints(bundle: Mapping[str, object]) -> tuple[GuidanceHint, ...]:
    hints: list[GuidanceHint] = []
    for head_name in (*REQUIRED_GUIDANCE_HEADS, *OPTIONAL_GUIDANCE_HEADS):
        hints.extend(guidance_head_hints(bundle, head_name))
    return tuple(sorted(hints, key=lambda row: (-float(row.priority), str(row.candidate_id))))


def build_guidance_ordering_report(
    *,
    candidate_kind: str,
    candidates: Iterable[Mapping[str, object]],
    hints: Iterable[GuidanceHint | Mapping[str, object]],
    enabled: bool,
) -> dict:
    """Return a pure ordering report; no candidates are accepted or rejected."""

    candidate_rows = tuple(dict(row) for row in candidates)
    typed_hints = normalize_guidance_hints(hints)
    priority_by_id = {hint.candidate_id: float(hint.priority) for hint in typed_hints}
    before_ids = tuple(_candidate_id(row, index) for index, row in enumerate(candidate_rows))
    indexed = tuple((index, row, before_ids[index]) for index, row in enumerate(candidate_rows))
    if enabled:
        ordered = tuple(
            sorted(
                indexed,
                key=lambda item: (
                    -float(priority_by_id.get(item[2], 0.0)),
                    item[0],
                ),
            )
        )
    else:
        ordered = indexed
    after_ids = tuple(row_id for _, _, row_id in ordered)
    after_rows = tuple(row for _, row, _ in ordered)
    candidate_set_preserved = sorted(before_ids) == sorted(after_ids)
    return {
        "schema_version": "lunar_ice_bpc.b5_guidance_ordering_report.v1",
        "candidate_kind": str(candidate_kind),
        "enabled": bool(enabled),
        "candidate_count": len(candidate_rows),
        "hint_count": len(typed_hints),
        "before_ids": list(before_ids),
        "after_ids": list(after_ids),
        "ordered_candidates": list(after_rows),
        "candidate_set_preserved": bool(candidate_set_preserved),
        "missing_hint_count": sum(1 for candidate_id in before_ids if candidate_id not in priority_by_id),
        "rejected_candidate_count": 0,
        "permanently_dropped_candidate_count": 0,
        "mutates_solver": False,
        "can_certify": False,
        "exact_status_effect": "none",
    }


def build_guidance_shadow_accounting(
    hints: Iterable[GuidanceHint | Mapping[str, object]],
    true_rc_candidates: Iterable[Mapping[str, object]],
    *,
    negative_eps: float = 1.0e-6,
    release_before_certificate: bool = True,
) -> dict:
    typed_hints = normalize_guidance_hints(hints)
    hint_by_id: dict[str, GuidanceHint] = {}
    for hint in typed_hints:
        hint_by_id.setdefault(hint.candidate_id, hint)
    proof_debt = ProofDebtQueue()
    candidate_labels: list[dict] = []
    debt_labels: list[dict] = []
    delayed_negative_count = 0
    delay_budget_exhausted_count = 0
    permanent_drop_count = 0
    for index, candidate in enumerate(true_rc_candidates):
        candidate_id = str(candidate.get("candidate_id") or candidate.get("id") or f"candidate_{index}")
        true_rc = None if candidate.get("true_reduced_cost") is None else float(candidate["true_reduced_cost"])
        hint = hint_by_id.get(candidate_id)
        is_negative = bool(true_rc is not None and true_rc < -abs(float(negative_eps)))
        accepted = bool(candidate.get("addability_accepted", candidate.get("accepted", True)))
        reject_reason = str(candidate.get("reject_reason") or "")
        delayed = bool(is_negative and hint is not None and int(hint.finite_delay_budget) > 0)
        if delayed:
            delayed_negative_count += 1
            proof_debt.add(
                {
                    "candidate_id": candidate_id,
                    "true_reduced_cost": true_rc,
                    "delay_source": hint.source,
                    "finite_delay_budget": hint.finite_delay_budget,
                }
            )
        if hint is not None and int(hint.finite_delay_budget) == 0 and delayed:
            delay_budget_exhausted_count += 1
        candidate_labels.append(
            {
                "label_type": "candidate_addability_label",
                "candidate_id": candidate_id,
                "true_reduced_cost": true_rc,
                "true_rc_negative": is_negative,
                "addability_accepted": accepted,
                "reject_reason": reject_reason,
                "hint_priority": None if hint is None else float(hint.priority),
                "hint_source": None if hint is None else str(hint.source),
            }
        )
        debt_labels.append(
            {
                "label_type": "delayed_negative_debt_label",
                "candidate_id": candidate_id,
                "true_rc_negative": is_negative,
                "delayed_by_guidance": delayed,
                "released_before_certificate": False,
                "rechecked_before_certificate": False,
            }
        )
    released = tuple()
    if release_before_certificate:
        released = proof_debt.release_all_before_certificate()
        released_ids = {row.candidate_id for row in released}
        debt_labels = [
            {
                **row,
                "released_before_certificate": str(row["candidate_id"]) in released_ids,
                "rechecked_before_certificate": str(row["candidate_id"]) in released_ids,
            }
            for row in debt_labels
        ]
    certificate_blocked = proof_debt.block_certificate_if_unreleased()
    if certificate_blocked:
        permanent_drop_count = proof_debt.audit()["blocking_true_rc_negative_count"]
    return {
        "schema_version": "lunar_ice_bpc.b5_guidance_shadow_accounting.v1",
        "mode": "shadow_only",
        "hint_count": len(typed_hints),
        "candidate_count": len(candidate_labels),
        "delayed_negative_count": delayed_negative_count,
        "released_before_certificate_count": len(released),
        "rechecked_before_certificate_count": len(released),
        "certificate_blocked_by_delayed_negative": bool(certificate_blocked),
        "delay_budget_exhausted_count": delay_budget_exhausted_count,
        "delayed_negative_caused_extra_cg_round_count": 0,
        "permanent_negative_drop_count": permanent_drop_count,
        "candidate_addability_labels": candidate_labels,
        "delayed_negative_debt_labels": debt_labels,
        "shadow_label_manifest": build_shadow_label_manifest(
            candidate_addability_labels=candidate_labels,
            delayed_negative_debt_labels=debt_labels,
        ),
        "proof_debt_queue": proof_debt.audit(),
        "guidance_can_construct_certificate": False,
        "guidance_can_mutate_exact_state": False,
        "mutates_solver": False,
        "can_certify": False,
        "exact_status_effect": "none",
    }


def build_shadow_label_manifest(
    *,
    candidate_addability_labels: Iterable[Mapping[str, object]],
    delayed_negative_debt_labels: Iterable[Mapping[str, object]],
    extra_label_counts: Mapping[str, int] | None = None,
) -> dict:
    addability_rows = tuple(candidate_addability_labels)
    debt_rows = tuple(delayed_negative_debt_labels)
    counts = {label: 0 for label in REQUIRED_SOLVER_ROI_LABELS}
    counts["candidate_addability_label"] = len(addability_rows)
    counts["delayed_negative_debt_label"] = len(debt_rows)
    counts["observed_true_rc_negative_found_by_final_judge"] = sum(
        1 for row in addability_rows if bool(row.get("true_rc_negative"))
    )
    for label, count in (extra_label_counts or {}).items():
        if str(label) in counts:
            counts[str(label)] = int(count)
    return {
        "schema_version": "lunar_ice_bpc.b5_shadow_label_manifest.v1",
        "required_solver_roi_labels": list(REQUIRED_SOLVER_ROI_LABELS),
        "label_counts": counts,
        "required_label_sections_present": all(label in counts for label in REQUIRED_SOLVER_ROI_LABELS),
        "mandatory_first_batch_labels_present": all(
            label in counts
            for label in ("candidate_addability_label", "delayed_negative_debt_label")
        ),
        "split_policy": {
            "main_split_keys": ["instance", "scale", "seed_family"],
            "random_row_split_allowed_for_debug_only": True,
            "random_row_split_is_main_claim": False,
        },
        "notes": (
            "Zero-count sections are explicit placeholders until the corresponding solver event appears; "
            "random-row split is never the main claim."
        ),
    }


def _candidate_id(row: Mapping[str, object], index: int) -> str:
    return str(row.get("candidate_id") or row.get("id") or f"candidate_{index}")


def _head_payload(
    raw: Mapping[str, object],
    heads: object,
    head_name: str,
) -> Iterable[GuidanceHint | Mapping[str, object]]:
    if isinstance(heads, MappingABC) and isinstance(heads.get(head_name), IterableABC):
        value = heads.get(head_name)
    else:
        value = raw.get(head_name)
    if value is None or isinstance(value, (str, bytes)):
        return tuple()
    if isinstance(value, (GuidanceHint, MappingABC)):
        return (value,)
    if isinstance(value, IterableABC):
        return tuple(row for row in value if isinstance(row, (GuidanceHint, MappingABC)))
    return tuple()


def _diagnostic_version_issues(
    *,
    ood_diagnostics: Mapping[str, object] | None,
    confidence_diagnostics: Mapping[str, object] | None,
    diagnostic_policy_versions: Mapping[str, object] | None,
) -> list[str]:
    versions = diagnostic_policy_versions or {}
    issues: list[str] = []
    if ood_diagnostics and not _has_any_key(
        ood_diagnostics,
        versions,
        ("ood_rule_version", "ood_rule_hash", "diagnostic_policy_version", "rule_version", "rule_hash"),
    ):
        issues.append("missing_ood_rule_version_or_hash")
    if confidence_diagnostics and not _has_any_key(
        confidence_diagnostics,
        versions,
        (
            "confidence_rule_version",
            "confidence_rule_hash",
            "threshold_version",
            "threshold_hash",
            "diagnostic_policy_version",
            "rule_version",
            "rule_hash",
        ),
    ):
        issues.append("missing_confidence_or_threshold_version_or_hash")
    return issues


def _has_any_key(
    primary: Mapping[str, object],
    fallback: Mapping[str, object],
    keys: Iterable[str],
) -> bool:
    for key in keys:
        if key in primary and str(primary[key]):
            return True
        if key in fallback and str(fallback[key]):
            return True
    return False
