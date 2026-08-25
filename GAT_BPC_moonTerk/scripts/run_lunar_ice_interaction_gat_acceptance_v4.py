#!/usr/bin/env python3
"""Install only the V4 dispatch, then run the frozen exact acceptance CLI."""

from __future__ import annotations

import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from lunar_ice_bpc.guidance.interaction_gat_queue_runtime_v4 import (  # noqa: E402
    INTERACTION_GAT_MANIFEST_ENV_V4,
    prepare_root_interaction_gat_request_v4_from_environment,
)


V1_DISPATCH_ENV = "LUNAR_ICE_P0V5_CONTEXT_QUEUE_PORTFOLIO_V1_MANIFEST"


def install_v4_dispatch() -> None:
    manifest = str(os.getenv(INTERACTION_GAT_MANIFEST_ENV_V4, "")).strip()
    if not manifest:
        raise SystemExit("V4 acceptance bootstrap requires a manifest")
    os.environ[V1_DISPATCH_ENV] = manifest
    import lunar_ice_bpc.guidance.context_queue_portfolio_runtime as dispatch
    dispatch.prepare_context_queue_portfolio_request_from_environment = (
        prepare_root_interaction_gat_request_v4_from_environment
    )


def main() -> int:
    install_v4_dispatch()
    import run_lunar_ice_native_spprc_acceptance as acceptance
    return int(acceptance.main())


if __name__ == "__main__":
    raise SystemExit(main())
