"""Adapter for the existing exact-safe Python resource-label engine."""

from __future__ import annotations

from lunar_ice_bpc.exact.bpc.pricing.backends.base import (
    BACKEND_MODE_EXACT_PROOF,
    BACKEND_OBJECTIVE_PHASE_ONE,
    BackendPricingRequest,
    BackendResult,
)


PYTHON_REFERENCE_BACKEND_ID = "python_reference"


class PythonReferenceBackend:
    backend_id = PYTHON_REFERENCE_BACKEND_ID

    def solve(self, request: BackendPricingRequest) -> BackendResult:
        if request.objective_mode == BACKEND_OBJECTIVE_PHASE_ONE:
            return BackendResult(
                backend_id=self.backend_id,
                engine_status="UNSUPPORTED_FEATURE",
                certificate_blockers=("python_reference_phase_one_objective_unsupported",),
            )
        from lunar_ice_bpc.exact.bpc.pricing.labeling_pricer import (
            EXACT_ELEMENTARY_MODE,
            LabelingPricingConfig,
            run_bpc_labeling_pricer,
        )

        payload, columns = run_bpc_labeling_pricer(
            request.data,
            request.true_duals,
            config=LabelingPricingConfig(
                mode=EXACT_ELEMENTARY_MODE,
                max_exact_tasks=len(request.data.task_ids),
                harvest_target=request.harvest_target,
                exact_negative_harvest_target=request.harvest_target,
                wall_time_limit_sec=request.wall_time_limit_sec,
                negative_eps=request.negative_eps,
                stop_at_first_negative=request.mode != BACKEND_MODE_EXACT_PROOF,
            ),
            branch_context=request.branch_context,
            cut_context=request.cut_context,
        )
        best = _optional_float(payload.get("true_best_reduced_cost"))
        exhaustive = bool(payload.get("pricing_complete_for_all_task_subsets"))
        certified = bool(payload.get("can_certify_no_negative"))
        blockers = []
        if not exhaustive:
            blockers.append("search_not_exhaustive")
        if payload.get("pricing_state") == "INCOMPLETE_LIMIT":
            blockers.append("python_reference_incomplete")
        return BackendResult(
            backend_id=self.backend_id,
            engine_status=str(payload.get("pricing_state") or ""),
            best_found_rc=best,
            global_min_rc=best if exhaustive and best is not None else None,
            global_min_rc_is_exact=bool(exhaustive and best is not None),
            proved_no_rc_below=(-request.negative_eps if certified else None),
            search_exhaustive=exhaustive,
            frontier_empty=exhaustive,
            labels_dropped=False,
            partial_columns_valid=True,
            columns=tuple(columns),
            certificate_blockers=tuple(dict.fromkeys(blockers)),
            telemetry={"python_reference_payload": payload},
        )


def _optional_float(value) -> float | None:
    return None if value is None else float(value)
