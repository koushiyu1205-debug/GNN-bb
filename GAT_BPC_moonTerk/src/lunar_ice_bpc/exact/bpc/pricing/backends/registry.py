"""Construction of pricing backends by stable identifier."""

from __future__ import annotations

from lunar_ice_bpc.exact.bpc.pricing.backends.native_rcspp import (
    NATIVE_DSSR_HOST_BACKEND_ID,
    NATIVE_DSSR_INPROCESS_BACKEND_ID,
    NATIVE_DSSR_V2_HOST_BACKEND_ID,
    NATIVE_DSSR_V2_INPROCESS_BACKEND_ID,
    NATIVE_HOST_BACKEND_ID,
    NATIVE_INPROCESS_BACKEND_ID,
    NATIVE_NG_DSSR_V3_HOST_BACKEND_ID,
    NATIVE_NG_DSSR_V3_INPROCESS_BACKEND_ID,
    NativeDssrHostBackend,
    NativeDssrInprocessBackend,
    NativeDssrV2HostBackend,
    NativeDssrV2InprocessBackend,
    NativeNgDssrV3HostBackend,
    NativeNgDssrV3InprocessBackend,
    NativeRcsppHostBackend,
    NativeRcsppInprocessBackend,
)
from lunar_ice_bpc.exact.bpc.pricing.backends.native_bidirectional_hybrid import (
    NATIVE_BIDIRECTIONAL_MIDPOINT_HYBRID_BACKEND_ID,
    NATIVE_BIDIRECTIONAL_MIDPOINT_PARTIAL_HYBRID_BACKEND_ID,
    NATIVE_BIDIRECTIONAL_ROOT_PARTIAL_HYBRID_BACKEND_ID,
    NativeBidirectionalMidpointHybridBackend,
    NativeBidirectionalMidpointPartialHybridBackend,
    NativeBidirectionalRootPartialHybridBackend,
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
        if value == NATIVE_DSSR_INPROCESS_BACKEND_ID:
            return NativeDssrInprocessBackend()
        if value == NATIVE_DSSR_HOST_BACKEND_ID:
            return NativeDssrHostBackend()
        if value == NATIVE_DSSR_V2_INPROCESS_BACKEND_ID:
            return NativeDssrV2InprocessBackend()
        if value == NATIVE_DSSR_V2_HOST_BACKEND_ID:
            return NativeDssrV2HostBackend()
        if value == NATIVE_NG_DSSR_V3_INPROCESS_BACKEND_ID:
            return NativeNgDssrV3InprocessBackend()
        if value == NATIVE_NG_DSSR_V3_HOST_BACKEND_ID:
            return NativeNgDssrV3HostBackend()
        if value == NATIVE_BIDIRECTIONAL_MIDPOINT_HYBRID_BACKEND_ID:
            return NativeBidirectionalMidpointHybridBackend()
        if (
            value
            == NATIVE_BIDIRECTIONAL_MIDPOINT_PARTIAL_HYBRID_BACKEND_ID
        ):
            return NativeBidirectionalMidpointPartialHybridBackend()
        if (
            value
            == NATIVE_BIDIRECTIONAL_ROOT_PARTIAL_HYBRID_BACKEND_ID
        ):
            return NativeBidirectionalRootPartialHybridBackend()
        raise ValueError(f"unknown pricing backend {backend_id!r}")

    @staticmethod
    def ids() -> tuple[str, ...]:
        return (
            PYTHON_REFERENCE_BACKEND_ID,
            NATIVE_INPROCESS_BACKEND_ID,
            NATIVE_HOST_BACKEND_ID,
            NATIVE_DSSR_INPROCESS_BACKEND_ID,
            NATIVE_DSSR_HOST_BACKEND_ID,
            NATIVE_DSSR_V2_INPROCESS_BACKEND_ID,
            NATIVE_DSSR_V2_HOST_BACKEND_ID,
            NATIVE_NG_DSSR_V3_INPROCESS_BACKEND_ID,
            NATIVE_NG_DSSR_V3_HOST_BACKEND_ID,
            NATIVE_BIDIRECTIONAL_MIDPOINT_HYBRID_BACKEND_ID,
            NATIVE_BIDIRECTIONAL_MIDPOINT_PARTIAL_HYBRID_BACKEND_ID,
            NATIVE_BIDIRECTIONAL_ROOT_PARTIAL_HYBRID_BACKEND_ID,
        )
