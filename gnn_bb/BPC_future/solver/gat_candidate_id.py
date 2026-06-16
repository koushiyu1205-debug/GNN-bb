"""Shared GAT admission candidate identifiers.

The online admission scheduler keys safe candidates by the journey signature.
Offline dataset/export code must use the same normalization so JSON-captured
signatures and in-memory ``JourneyColumn.signature`` values hash identically.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from typing import Any


def normalize_journey_signature(signature: Any) -> Any:
    if signature is None:
        return tuple()
    if isinstance(signature, tuple):
        return tuple(normalize_journey_signature(item) for item in signature)
    if isinstance(signature, list):
        return tuple(normalize_journey_signature(item) for item in signature)
    if isinstance(signature, Mapping):
        return tuple(
            (str(key), normalize_journey_signature(value))
            for key, value in sorted(signature.items(), key=lambda item: str(item[0]))
        )
    return signature


def journey_gat_candidate_id_from_signature(signature: Any) -> str:
    payload = repr(normalize_journey_signature(signature))
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def journey_gat_candidate_id(journey: Any) -> str:
    if isinstance(journey, Mapping):
        signature = journey.get("signature")
    else:
        signature = getattr(journey, "signature", tuple())
    return journey_gat_candidate_id_from_signature(signature)
