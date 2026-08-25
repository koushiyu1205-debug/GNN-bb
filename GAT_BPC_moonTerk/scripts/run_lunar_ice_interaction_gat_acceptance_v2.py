#!/usr/bin/env python3
"""Run the exact acceptance entrypoint with V2 runtime dispatch installed.

The frozen exact solver has one optional context-portfolio hook.  V2 reuses
that hook in a fresh process by replacing only the Python callable exported by
the V1 guidance module.  Exact/Native source, comparator semantics, and the
engine hash remain unchanged; all arguments and the exit status are delegated
to the normal acceptance runner.
"""

from __future__ import annotations

import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from lunar_ice_bpc.guidance.interaction_gat_queue_runtime_v2 import (  # noqa: E402
    INTERACTION_GAT_MANIFEST_ENV,
    prepare_root_interaction_gat_request_from_environment,
)


# The exact integration checks this legacy environment variable before doing
# the late import.  Its value is never parsed because the exported function is
# rebound below.  Keeping this adapter outside exact/ is what permits the
# pre-action r1 snapshots to retain their frozen exact-source binding.
V1_DISPATCH_ENV = "LUNAR_ICE_P0V5_CONTEXT_QUEUE_PORTFOLIO_V1_MANIFEST"


def install_v2_dispatch() -> None:
    manifest = str(os.getenv(INTERACTION_GAT_MANIFEST_ENV, "")).strip()
    if not manifest:
        raise SystemExit("V2 acceptance bootstrap requires a manifest")
    os.environ[V1_DISPATCH_ENV] = manifest
    import lunar_ice_bpc.guidance.context_queue_portfolio_runtime as dispatch

    dispatch.prepare_context_queue_portfolio_request_from_environment = (
        prepare_root_interaction_gat_request_from_environment
    )


def main() -> int:
    install_v2_dispatch()
    import run_lunar_ice_native_spprc_acceptance as acceptance

    return int(acceptance.main())


if __name__ == "__main__":
    raise SystemExit(main())
