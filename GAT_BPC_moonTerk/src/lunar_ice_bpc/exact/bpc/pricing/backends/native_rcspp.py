"""Project-local adapters for the pinned lab-core/rcspp extension."""

from __future__ import annotations

import atexit
from collections import OrderedDict
from dataclasses import fields, replace
import hashlib
import importlib
import json
import multiprocessing
import os
from pathlib import Path
import threading
from time import monotonic, sleep
from typing import Any
import weakref

from lunar_ice_bpc.domain.scenario import PATH_TYPES
from lunar_ice_bpc.exact.bpc.pricing.backends.base import (
    BACKEND_MODE_EXACT_PROOF,
    BACKEND_OBJECTIVE_PHASE_ONE,
    BackendPricingRequest,
    BackendResult,
)
from lunar_ice_bpc.exact.core.branching import branch_context_from_payload
from lunar_ice_bpc.exact.core.cuts import cut_context_from_payload
from lunar_ice_bpc.exact.core.columns import build_timed_sortie
from lunar_ice_bpc.exact.core.journey import build_journey_column
from lunar_ice_bpc.exact.core.objective import objective_references
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals, manual_journey_reduced_cost


NATIVE_INPROCESS_BACKEND_ID = "native_rcspp_inprocess"
NATIVE_HOST_BACKEND_ID = "native_rcspp_host"
NATIVE_HOST_PROTOCOL = "lunar_spprc_host.v1"
_STATIC_PAYLOAD_CACHE_LOCK = threading.RLock()
_STATIC_PAYLOAD_CACHE: OrderedDict[int, tuple[weakref.ReferenceType, dict]] = OrderedDict()
_STATIC_PAYLOAD_CACHE_MAX_ENTRIES = 16


class NativeRcsppInprocessBackend:
    backend_id = NATIVE_INPROCESS_BACKEND_ID

    def solve(self, request: BackendPricingRequest) -> BackendResult:
        capability_blockers = _capability_blockers(request)
        if capability_blockers:
            return _empty_result(
                self.backend_id,
                "UNSUPPORTED_FEATURE",
                blockers=capability_blockers,
            )
        binding_blockers = _binding_blockers(request)
        if binding_blockers:
            return _empty_result(self.backend_id, "HASH_MISMATCH", blockers=binding_blockers)
        try:
            native = importlib.import_module("lunar_spprc_native")
        except Exception as exc:
            return _empty_result(
                self.backend_id,
                "BACKEND_UNAVAILABLE",
                blockers=("native_extension_unavailable",),
                telemetry={"error": repr(exc)},
            )

        try:
            raw = dict(native.solve(_native_request_payload(request)))
        except Exception as exc:
            return _empty_result(
                self.backend_id,
                "BACKEND_ERROR",
                blockers=("native_backend_exception",),
                telemetry={"error": repr(exc)},
            )
        return _audit_native_result(request, raw, backend_id=self.backend_id)


class NativeRcsppHostBackend:
    """Persistent crash/RSS-isolated host with same-instance delta IPC."""

    backend_id = NATIVE_HOST_BACKEND_ID
    _runtime: _PersistentHostRuntime | None = None
    _lock = threading.RLock()

    def solve(self, request: BackendPricingRequest) -> BackendResult:
        capability_blockers = _capability_blockers(request)
        if capability_blockers:
            return _empty_result(
                self.backend_id,
                "UNSUPPORTED_FEATURE",
                blockers=capability_blockers,
            )
        with self._lock:
            if self.__class__._runtime is None:
                self.__class__._runtime = _PersistentHostRuntime()
            return self.__class__._runtime.solve(request)

    @classmethod
    def close(cls) -> None:
        with cls._lock:
            if cls._runtime is not None:
                cls._runtime.close()
                cls._runtime = None


class _PersistentHostRuntime:
    def __init__(self) -> None:
        self.context = multiprocessing.get_context("spawn")
        self.process = None
        self.connection = None
        self.build_hash = ""
        self.loaded_instance_hash = ""
        self.request_count = 0
        self.next_request_id = 1

    def solve(self, request: BackendPricingRequest) -> BackendResult:
        expected_hash = _host_build_hash()
        stale_restarted = False
        if not self._ready() or self.build_hash != expected_hash:
            stale = bool(self._ready() and self.build_hash != expected_hash)
            stale_restarted = stale
            self.close()
            start_error = self._start(expected_hash)
            if start_error:
                return _empty_result(
                    NATIVE_HOST_BACKEND_ID,
                    "HASH_MISMATCH" if stale else "BACKEND_UNAVAILABLE",
                    blockers=(
                        "stale_host_build_hash" if stale else "host_startup_failed",
                    ),
                    telemetry={"error": start_error},
                )

        from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import spprc_instance_hash

        instance_hash = request.instance_hash or spprc_instance_hash(request.data)
        request_id = self.next_request_id
        self.next_request_id += 1
        reused = self.request_count > 0
        same_instance = bool(self.loaded_instance_hash == instance_hash)
        request_kind = "solve_delta" if same_instance else "load_solve"
        message = {
            "protocol": NATIVE_HOST_PROTOCOL,
            "kind": request_kind,
            "request_id": request_id,
            "expected_build_hash": expected_hash,
            "instance_hash": instance_hash,
            "request": _request_ipc_payload(request, include_data=not same_instance),
        }
        try:
            self.connection.send(message)
        except (BrokenPipeError, EOFError, OSError, TypeError) as exc:
            exitcode = None if self.process is None else self.process.exitcode
            self.close()
            return _empty_result(
                NATIVE_HOST_BACKEND_ID,
                "BACKEND_CRASH",
                blockers=("host_send_failed",),
                telemetry={"error": repr(exc), "host_exitcode": exitcode},
            )

        deadline = (
            monotonic() + float(request.wall_time_limit_sec) + 1.0
            if request.wall_time_limit_sec is not None
            else None
        )
        rss_limit_bytes = int(float(request.memory_limit_gb) * (1024**3))
        peak_rss = 0
        stop_reason = ""
        try:
            while self._ready() and not self.connection.poll(0.05):
                rss = _process_rss_bytes(self.process.pid)
                peak_rss = max(peak_rss, rss)
                if deadline is not None and monotonic() >= deadline:
                    stop_reason = "TIMEOUT"
                    break
                if rss_limit_bytes > 0 and rss >= rss_limit_bytes:
                    stop_reason = "MEMORY_LIMIT"
                    break
                sleep(0.01)
        except KeyboardInterrupt:
            self.close()
            raise
        if stop_reason:
            exitcode = self._terminate()
            return _empty_result(
                NATIVE_HOST_BACKEND_ID,
                stop_reason,
                blockers=(f"host_{stop_reason.lower()}",),
                telemetry={
                    "host_exitcode": exitcode,
                    "host_peak_rss_bytes": peak_rss,
                    "host_partial_result_received": False,
                    "host_proof_state_discarded": True,
                },
            )
        if not self._ready() and not self.connection.poll(0.1):
            exitcode = None if self.process is None else self.process.exitcode
            self.close()
            return _empty_result(
                NATIVE_HOST_BACKEND_ID,
                "BACKEND_CRASH",
                blockers=("host_crashed_without_result",),
                telemetry={
                    "host_exitcode": exitcode,
                    "host_peak_rss_bytes": peak_rss,
                    "host_partial_result_received": False,
                },
            )
        try:
            response = self.connection.recv()
        except (EOFError, OSError) as exc:
            exitcode = None if self.process is None else self.process.exitcode
            self.close()
            return _empty_result(
                NATIVE_HOST_BACKEND_ID,
                "BACKEND_CRASH",
                blockers=("host_response_failed",),
                telemetry={"error": repr(exc), "host_exitcode": exitcode},
            )
        if (
            response.get("protocol") != NATIVE_HOST_PROTOCOL
            or int(response.get("request_id") or -1) != request_id
            or response.get("build_hash") != expected_hash
            or response.get("instance_hash") != instance_hash
        ):
            self.close()
            return _empty_result(
                NATIVE_HOST_BACKEND_ID,
                "HASH_MISMATCH",
                blockers=("stale_host_response_binding",),
                telemetry={"response": repr(response)[:1000]},
            )
        if response.get("kind") != "ok":
            return _empty_result(
                NATIVE_HOST_BACKEND_ID,
                "BACKEND_ERROR",
                blockers=("host_backend_exception",),
                telemetry={"error": response.get("error")},
            )
        self.loaded_instance_hash = instance_hash
        self.request_count += 1
        result = response["result"]
        telemetry = dict(result.telemetry or {})
        telemetry.update(
            {
                "host_protocol": NATIVE_HOST_PROTOCOL,
                "host_pid": self.process.pid,
                "host_reused": reused,
                "host_same_instance_delta": same_instance,
                "host_request_kind": request_kind,
                "host_request_count": self.request_count,
                "host_peak_rss_bytes": peak_rss,
                "host_build_hash": expected_hash,
                "host_stale_restarted": stale_restarted,
                "host_partial_result_received": bool(result.columns),
                "host_proof_state_discarded": not result.search_exhaustive,
            }
        )
        return replace(
            result,
            backend_id=NATIVE_HOST_BACKEND_ID,
            telemetry=telemetry,
        )

    def _start(self, expected_hash: str) -> str:
        parent, child = self.context.Pipe(duplex=True)
        process = self.context.Process(
            target=_persistent_host_main,
            args=(child,),
            daemon=True,
        )
        process.start()
        child.close()
        self.process = process
        self.connection = parent
        if not parent.poll(10.0):
            self.close()
            return "host handshake timed out"
        try:
            response = parent.recv()
        except (EOFError, OSError) as exc:
            self.close()
            return repr(exc)
        if (
            response.get("protocol") != NATIVE_HOST_PROTOCOL
            or response.get("kind") != "ready"
            or response.get("build_hash") != expected_hash
        ):
            self.close()
            return f"invalid host handshake: {response!r}"
        self.build_hash = expected_hash
        self.loaded_instance_hash = ""
        self.request_count = 0
        return ""

    def _ready(self) -> bool:
        return bool(
            self.process is not None
            and self.connection is not None
            and self.process.is_alive()
        )

    def _terminate(self):
        process = self.process
        if process is None:
            self.close()
            return None
        process.terminate()
        process.join(timeout=2.0)
        if process.is_alive():
            process.kill()
            process.join(timeout=1.0)
        exitcode = process.exitcode
        self.close()
        return exitcode

    def close(self) -> None:
        process = self.process
        connection = self.connection
        if process is not None and process.is_alive() and connection is not None:
            try:
                connection.send({"protocol": NATIVE_HOST_PROTOCOL, "kind": "shutdown"})
            except (BrokenPipeError, EOFError, OSError):
                pass
            process.join(timeout=1.0)
            if process.is_alive():
                process.terminate()
                process.join(timeout=1.0)
        if connection is not None:
            connection.close()
        self.process = None
        self.connection = None
        self.build_hash = ""
        self.loaded_instance_hash = ""
        self.request_count = 0


def _request_ipc_payload(
    request: BackendPricingRequest,
    *,
    include_data: bool,
) -> dict:
    """Return the versioned, pickle-safe host request schema.

    HiGHS exposes some dual maps as ``mappingproxy`` objects.  Passing the
    domain request directly through ``multiprocessing`` therefore depends on
    an implementation detail that is not pickleable.  Normalize every mutable
    request component here and reconstruct the typed request in the host.
    The immutable instance graph is sent only on ``load_solve``; subsequent
    same-instance calls carry a small delta.
    """

    payload = {
        field.name: getattr(request, field.name)
        for field in fields(BackendPricingRequest)
        if field.name
        not in {"data", "true_duals", "branch_context", "cut_context"}
    }
    payload.update(
        {
            "schema_version": NATIVE_HOST_PROTOCOL,
            "true_duals": {
                "cover": {
                    str(key): float(value)
                    for key, value in request.true_duals.cover.items()
                },
                "fleet_limit": float(request.true_duals.fleet_limit),
                "cuts": {
                    str(key): float(value)
                    for key, value in (request.true_duals.cuts or {}).items()
                },
            },
            "branch_context": request.branch_context.to_payload(),
            "cut_context": request.cut_context.to_payload(),
        }
    )
    if include_data:
        payload["data"] = request.data
    return payload


def _request_from_ipc_payload(
    payload: dict,
    *,
    base_request: BackendPricingRequest | None = None,
) -> BackendPricingRequest:
    if payload.get("schema_version") != NATIVE_HOST_PROTOCOL:
        raise RuntimeError("host request schema version mismatch")
    data = payload.get("data") if "data" in payload else None
    if data is None:
        if base_request is None:
            raise RuntimeError("host delta request has no loaded instance")
        data = base_request.data
    dual_payload = dict(payload.get("true_duals") or {})
    values = {
        field.name: payload[field.name]
        for field in fields(BackendPricingRequest)
        if field.name
        not in {"data", "true_duals", "branch_context", "cut_context"}
        and field.name in payload
    }
    values.update(
        {
            "data": data,
            "true_duals": JourneyDuals(
                cover=dict(dual_payload.get("cover") or {}),
                fleet_limit=float(dual_payload.get("fleet_limit") or 0.0),
                cuts=dict(dual_payload.get("cuts") or {}),
            ),
            "branch_context": branch_context_from_payload(
                payload.get("branch_context")
            ),
            "cut_context": cut_context_from_payload(payload.get("cut_context")),
        }
    )
    if base_request is not None:
        return replace(base_request, **values)
    return BackendPricingRequest(**values)


def _host_build_hash() -> str:
    from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import spprc_engine_build_hash

    return spprc_engine_build_hash(NATIVE_HOST_BACKEND_ID)


def _persistent_host_main(connection) -> None:
    build_hash = _host_build_hash()
    base_request = None
    loaded_instance_hash = ""
    connection.send(
        {
            "protocol": NATIVE_HOST_PROTOCOL,
            "kind": "ready",
            "build_hash": build_hash,
            "pid": os.getpid(),
        }
    )
    while True:
        try:
            message = connection.recv()
        except EOFError:
            break
        if message.get("protocol") != NATIVE_HOST_PROTOCOL:
            break
        if message.get("kind") == "shutdown":
            break
        request_id = int(message.get("request_id") or 0)
        instance_hash = str(message.get("instance_hash") or "")
        response = {
            "protocol": NATIVE_HOST_PROTOCOL,
            "request_id": request_id,
            "build_hash": build_hash,
            "instance_hash": instance_hash,
        }
        try:
            if message.get("expected_build_hash") != build_hash:
                raise RuntimeError("host build hash is stale")
            if message.get("kind") == "load_solve":
                base_request = _request_from_ipc_payload(message["request"])
                loaded_instance_hash = instance_hash
            elif message.get("kind") == "solve_delta":
                if base_request is None or loaded_instance_hash != instance_hash:
                    raise RuntimeError("host delta request does not match loaded instance")
                base_request = _request_from_ipc_payload(
                    message["request"],
                    base_request=base_request,
                )
            else:
                raise RuntimeError(f"unsupported host request kind {message.get('kind')!r}")
            result = NativeRcsppInprocessBackend().solve(base_request)
            response.update({"kind": "ok", "result": result})
        except BaseException as exc:  # pragma: no cover - protects the parent process
            response.update({"kind": "error", "error": repr(exc)})
        connection.send(response)
    connection.close()


atexit.register(NativeRcsppHostBackend.close)


def _capability_blockers(request: BackendPricingRequest) -> tuple[str, ...]:
    blockers: list[str] = []
    if not request.cut_context.empty and not request.cut_state_enabled:
        blockers.append("native_nonempty_cut_context_not_promoted")
    if request.objective_mode == BACKEND_OBJECTIVE_PHASE_ONE and not request.cut_context.empty:
        blockers.append("native_phase_one_nonempty_cut_context_unsupported")
    if len(request.data.task_ids) > 100:
        blockers.append("native_v1_task_count_above_100")
    return tuple(blockers)


def _binding_blockers(request: BackendPricingRequest) -> tuple[str, ...]:
    from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import spprc_instance_hash

    blockers = []
    if request.instance_hash and request.instance_hash != spprc_instance_hash(request.data):
        blockers.append("native_instance_hash_mismatch")
    if request.dual_binding_hash and request.dual_binding_hash != _stable_hash(
        {
            "cover": sorted(
                (str(key), float(value)) for key, value in request.true_duals.cover.items()
            ),
            "fleet_limit": float(request.true_duals.fleet_limit),
            "cuts": sorted(
                (str(key), float(value))
                for key, value in (request.true_duals.cuts or {}).items()
            ),
        }
    ):
        blockers.append("native_dual_binding_hash_mismatch")
    if request.branch_context_hash not in {"", "empty"} and request.branch_context_hash != _stable_hash(
        request.branch_context.to_payload()
    ):
        blockers.append("native_branch_context_hash_mismatch")
    if request.cut_context_hash not in {"", "empty"} and request.cut_context_hash != _stable_hash(
        request.cut_context.to_payload()
    ):
        blockers.append("native_cut_context_hash_mismatch")
    return tuple(blockers)


def _stable_hash(payload) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def _native_request_payload(request: BackendPricingRequest) -> dict:
    data = request.data
    static = _native_static_payload(data)
    tasks = [
        {
            **row,
            "dual": float(request.true_duals.cover.get(row["id"], 0.0)),
        }
        for row in static["tasks"]
    ]
    return {
        **static,
        "tasks": tasks,
        "branch_decisions": [
            decision.to_payload() for decision in request.branch_context.pair_decisions
        ],
        "cuts": [
            {
                **cut.to_payload(),
                "dual": float((request.true_duals.cuts or {}).get(cut.cut_id, 0.0)),
            }
            for cut in request.cut_context.cuts
        ],
        "weight_cost": (
            0.0
            if request.objective_mode == BACKEND_OBJECTIVE_PHASE_ONE
            else data.objective.weight_operating_cost
        ),
        "weight_risk": (
            0.0
            if request.objective_mode == BACKEND_OBJECTIVE_PHASE_ONE
            else data.objective.weight_risk
        ),
        "weight_completion": (
            0.0
            if request.objective_mode == BACKEND_OBJECTIVE_PHASE_ONE
            else data.objective.weight_completion
        ),
        "fleet_dual": request.true_duals.fleet_limit,
        "mode": request.mode,
        "objective_mode": request.objective_mode,
        "harvest_target": request.harvest_target,
        "wall_time_limit_sec": request.wall_time_limit_sec,
        "memory_limit_gb": request.memory_limit_gb,
        "negative_eps": request.negative_eps,
        "dominance_eps": request.dominance_eps,
        "resource_eps": request.resource_eps,
        "instance_hash": request.instance_hash or static["instance_hash"],
        "graph_cache_entries": max(
            0,
            int(os.getenv("LUNAR_ICE_SPPRC_GRAPH_CACHE_ENTRIES", "1")),
        ),
        "completion_bound_enabled": bool(
            request.completion_bound_enabled and request.cut_context.empty
        ),
        # Preserve the candidate-column surface in negative-harvest calls.
        # Subset dominance is a proof accelerator: it preserves the optimum
        # and no-negative result, but can intentionally omit dominated
        # negative task-set variants.
        "subset_dominance_enabled": bool(
            request.subset_dominance_enabled and request.exact_proof_mode
        ),
        "config_hash": request.config_hash,
        "dual_binding_hash": request.dual_binding_hash,
    }


def _native_static_payload(data) -> dict:
    from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import spprc_instance_hash

    cache_key = id(data)
    with _STATIC_PAYLOAD_CACHE_LOCK:
        cached = _STATIC_PAYLOAD_CACHE.get(cache_key)
        if cached is not None and cached[0]() is data:
            _STATIC_PAYLOAD_CACHE.move_to_end(cache_key)
            return cached[1]
    refs = objective_references(data)
    task_index = {task_id: index for index, task_id in enumerate(data.task_ids)}
    tasks = []
    for task_id in data.task_ids:
        task = data.tasks[task_id]
        tasks.append(
            {
                "id": task_id,
                "index": task_index[task_id],
                "science_weight": task.science_weight,
                "demand": task.demand,
                "service_time": task.service_time,
                "service_energy": task.service_energy,
                "service_cost": task.service_cost,
                "ready_time": task.ready_time,
                "due_time": task.due_time,
                "local_shadow_score": task.local_shadow_score,
                "local_thermal_risk": task.local_thermal_risk,
            }
        )
    arcs = []
    for (source, target), by_type in sorted(data.arcs.items()):
        for path_type in PATH_TYPES:
            option = by_type[path_type]
            arcs.append(
                {
                    "source": source,
                    "target": target,
                    "path_type": path_type,
                    "travel_time": option.travel_time_min,
                    "energy": option.energy_proxy,
                    "risk": option.risk_integral,
                    "distance": option.distance_km,
                    "shadow": option.shadow_exposure_min,
                }
            )
    value = {
        "instance_id": data.instance_id,
        "instance_hash": spprc_instance_hash(data),
        "tasks": tasks,
        "arcs": arcs,
        "max_tasks_per_trip": data.max_tasks_per_trip,
        "capacity": data.capacity,
        "energy_limit": data.energy_limit,
        "horizon": data.horizon,
        "dock_overhead": data.dock_overhead_min,
        "recharge_power": data.recharge_power_proxy_per_min,
        "shadow_limit": data.max_shadow_exposure_per_sortie,
        "reference_cost": refs.reference_cost,
        "reference_risk": refs.reference_risk,
        "reference_completion": refs.reference_completion,
    }
    with _STATIC_PAYLOAD_CACHE_LOCK:
        _STATIC_PAYLOAD_CACHE[cache_key] = (weakref.ref(data), value)
        _STATIC_PAYLOAD_CACHE.move_to_end(cache_key)
        while len(_STATIC_PAYLOAD_CACHE) > _STATIC_PAYLOAD_CACHE_MAX_ENTRIES:
            _STATIC_PAYLOAD_CACHE.popitem(last=False)
    return value


def _audit_native_result(
    request: BackendPricingRequest,
    raw: dict[str, Any],
    *,
    backend_id: str,
) -> BackendResult:
    blockers = [str(item) for item in raw.get("certificate_blockers", [])]
    columns = []
    audited_rcs = []
    reconstruction_rows = []
    for route in raw.get("routes", []) or []:
        try:
            column = _reconstruct_column(request, route)
            manual_rc = float(_manual_backend_reduced_cost(column, request))
            native_rc = float(route["reduced_cost"])
            rc_delta = abs(native_rc - manual_rc)
            if rc_delta > request.reconstruction_eps:
                blockers.append("native_python_reduced_cost_mismatch")
                reconstruction_rows.append(
                    {"native_rc": native_rc, "manual_rc": manual_rc, "delta": rc_delta, "accepted": False}
                )
                continue
            reconstruction_rows.append(
                {"native_rc": native_rc, "manual_rc": manual_rc, "delta": rc_delta, "accepted": True}
            )
            if manual_rc < -request.negative_eps:
                columns.append(column)
                audited_rcs.append(manual_rc)
        except Exception as exc:
            blockers.append("native_route_reconstruction_failed")
            reconstruction_rows.append({"accepted": False, "error": repr(exc)})

    engine_status = str(raw.get("status") or "UNKNOWN").upper()
    exhaustive = bool(raw.get("search_exhaustive")) and engine_status == "COMPLETE"
    frontier_empty = bool(raw.get("frontier_empty")) and exhaustive
    labels_dropped = bool(raw.get("labels_dropped"))
    if labels_dropped:
        blockers.append("native_labels_dropped")
    if request.exact_proof_mode and not exhaustive:
        blockers.append("native_exact_search_incomplete")
    if request.exact_proof_mode and not frontier_empty:
        blockers.append("native_frontier_not_empty")

    if not request.exact_proof_mode and columns:
        best_by_task_set = {}
        for column, manual_rc in zip(columns, audited_rcs):
            key = frozenset(column.task_set)
            current = best_by_task_set.get(key)
            if current is None or manual_rc < current[0]:
                best_by_task_set[key] = (manual_rc, column)
        selected = sorted(best_by_task_set.values(), key=lambda row: row[0])[
            : request.harvest_target
        ]
        audited_rcs = [row[0] for row in selected]
        columns = [row[1] for row in selected]

    best_found = min(audited_rcs) if audited_rcs else None
    global_min = best_found if exhaustive and best_found is not None else None
    proved_threshold = (
        -request.negative_eps
        if exhaustive and frontier_empty and not audited_rcs and not blockers
        else None
    )
    telemetry = dict(raw.get("telemetry") or {})
    telemetry.update(
        {
            "native_raw_best_found_rc": raw.get("best_found_rc"),
            "native_build_info": raw.get("build_info") or {},
            "reconstruction_audit": reconstruction_rows,
        }
    )
    return BackendResult(
        backend_id=backend_id,
        engine_status=engine_status,
        best_found_rc=best_found,
        global_min_rc=global_min,
        global_min_rc_is_exact=bool(global_min is not None),
        proved_no_rc_below=proved_threshold,
        unexplored_rc_lower_bound=_optional_float(raw.get("unexplored_rc_lower_bound")),
        search_exhaustive=exhaustive,
        frontier_empty=frontier_empty,
        labels_dropped=labels_dropped,
        partial_columns_valid=bool(reconstruction_rows and all(row.get("accepted") for row in reconstruction_rows)),
        columns=tuple(columns),
        certificate_blockers=tuple(dict.fromkeys(blockers)),
        telemetry=telemetry,
    )


def _reconstruct_column(request: BackendPricingRequest, route: dict):
    start_time = 0.0
    sorties = []
    for row in route.get("sorties", []) or []:
        tasks = tuple(str(task_id) for task_id in row.get("tasks", []))
        path_types = tuple(str(path_type) for path_type in row.get("path_types", []))
        if not tasks or len(path_types) != len(tasks) + 1:
            raise ValueError("native sortie path is incomplete")
        sortie = build_timed_sortie(request.data, tasks, path_types, start_time=start_time)
        if not sortie.feasible:
            raise ValueError(f"native route reconstructed infeasible: {sortie.infeasible_reason}")
        sorties.append(sortie)
        start_time = float(sortie.end_time)
    if not sorties:
        raise ValueError("native route contains no nonempty sortie")
    return build_journey_column(request.data, tuple(sorties))


def _manual_backend_reduced_cost(column, request: BackendPricingRequest) -> float:
    if request.objective_mode != BACKEND_OBJECTIVE_PHASE_ONE:
        return manual_journey_reduced_cost(
            column,
            request.true_duals,
            cut_coefficients=request.cut_context.coefficients_for(column),
        )
    value = -float(request.true_duals.fleet_limit)
    for task_id in column.task_set:
        value -= float(request.true_duals.cover.get(str(task_id), 0.0))
    # Phase-I is promoted only for empty CutContext.  Keep this assertion at
    # the final audit boundary so a future cut integration cannot silently
    # reuse official-objective arithmetic.
    if not request.cut_context.empty or request.true_duals.cuts:
        raise ValueError("phase-one native reduced cost requires empty cut context")
    return round(value, 9)


def _empty_result(
    backend_id: str,
    status: str,
    *,
    blockers: tuple[str, ...],
    telemetry: dict | None = None,
) -> BackendResult:
    return BackendResult(
        backend_id=backend_id,
        engine_status=status,
        certificate_blockers=tuple(blockers),
        telemetry=dict(telemetry or {}),
    )


def _process_rss_bytes(pid: int | None) -> int:
    if not pid:
        return 0
    try:
        for line in Path(f"/proc/{pid}/status").read_text(encoding="utf-8").splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) * 1024
    except (FileNotFoundError, PermissionError, ProcessLookupError, ValueError):
        return 0
    return 0


def effective_memory_limit_gb(nominal_gb: float) -> float:
    """Return min(profile limit, 70% physical RAM), without optional dependencies."""

    pages = os.sysconf("SC_PHYS_PAGES")
    page_size = os.sysconf("SC_PAGE_SIZE")
    physical_gb = float(pages * page_size) / float(1024**3)
    return min(max(0.0, float(nominal_gb)), 0.70 * physical_gb)


def _optional_float(value) -> float | None:
    return None if value is None else float(value)
