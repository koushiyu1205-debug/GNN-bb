#!/usr/bin/env python3
"""Verify the frozen V7 manifest/config binding, then run exact acceptance."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lunar_ice_bpc.guidance.frontier_gat_qd1_runtime_v7 import (  # noqa: E402
    MANIFEST_ENV,
)


def main() -> int:
    manifest_value = str(os.getenv(MANIFEST_ENV, "")).strip()
    if not manifest_value:
        raise SystemExit("V7 acceptance bootstrap requires a manifest")
    manifest = json.loads(Path(manifest_value).read_text(encoding="utf-8"))
    try:
        config_index = sys.argv.index("--config") + 1
        config_path = Path(sys.argv[config_index]).resolve()
    except (ValueError, IndexError) as exc:
        raise SystemExit("V7 acceptance requires an explicit --config") from exc
    observed = hashlib.sha256(config_path.read_bytes()).hexdigest()
    if observed != str(manifest["selected_exact_config_sha256"]):
        raise SystemExit("V7 selected exact config hash drift")
    import run_lunar_ice_native_spprc_acceptance as acceptance
    return int(acceptance.main())


if __name__ == "__main__":
    raise SystemExit(main())
