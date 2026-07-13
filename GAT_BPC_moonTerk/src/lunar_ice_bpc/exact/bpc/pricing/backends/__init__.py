"""Pricing backend registry for exact-safe SPPRC execution."""

from lunar_ice_bpc.exact.bpc.pricing.backends.base import (
    BACKEND_MODE_EXACT_PROOF,
    BACKEND_MODE_NEGATIVE_HARVEST,
    BACKEND_OBJECTIVE_OFFICIAL,
    BACKEND_OBJECTIVE_PHASE_ONE,
    BackendPricingRequest,
    BackendResult,
    PricingBackend,
)
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
from lunar_ice_bpc.exact.bpc.pricing.backends.registry import BackendRegistry
from lunar_ice_bpc.exact.bpc.pricing.backends.scale_profiles import (
    DEFAULT_NATIVE_SPPRC_SCALE_PROFILES,
    NativeSpprcScaleProfile,
    native_spprc_scale_profile,
)

__all__ = [
    "BACKEND_MODE_EXACT_PROOF",
    "BACKEND_MODE_NEGATIVE_HARVEST",
    "BACKEND_OBJECTIVE_OFFICIAL",
    "BACKEND_OBJECTIVE_PHASE_ONE",
    "BackendPricingRequest",
    "BackendRegistry",
    "BackendResult",
    "DEFAULT_NATIVE_SPPRC_SCALE_PROFILES",
    "NATIVE_HOST_BACKEND_ID",
    "NATIVE_INPROCESS_BACKEND_ID",
    "NativeRcsppHostBackend",
    "NativeRcsppInprocessBackend",
    "NativeSpprcScaleProfile",
    "PYTHON_REFERENCE_BACKEND_ID",
    "PricingBackend",
    "PythonReferenceBackend",
    "native_spprc_scale_profile",
]
