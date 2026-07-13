"""Construction of pricing backends by stable identifier."""

from __future__ import annotations

from lunar_ice_bpc.exact.bpc.pricing.backends.native_rcspp import (
    NATIVE_HOST_BACKEND_ID,
    NATIVE_INPROCESS_BACKEND_ID,
    NativeRcsppHostBackend,
    NativeRcsppInprocessBackend,
)
from lunar_ice_bpc.exact.bpc.pricing.backends.python_reference import (
    PYTHON_REFERENCE_BACKEND_ID,
    PythonReferenceBackend,
)


class BackendRegistry:
    @staticmethod
    def create(backend_id: str):
        value = str(backend_id)
        if value == PYTHON_REFERENCE_BACKEND_ID:
            return PythonReferenceBackend()
        if value == NATIVE_INPROCESS_BACKEND_ID:
            return NativeRcsppInprocessBackend()
        if value == NATIVE_HOST_BACKEND_ID:
            return NativeRcsppHostBackend()
        raise ValueError(f"unknown pricing backend {backend_id!r}")

    @staticmethod
    def ids() -> tuple[str, ...]:
        return (
            PYTHON_REFERENCE_BACKEND_ID,
            NATIVE_INPROCESS_BACKEND_ID,
            NATIVE_HOST_BACKEND_ID,
        )
