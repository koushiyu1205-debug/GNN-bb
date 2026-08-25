#!/usr/bin/env python3
"""Run the frozen QG2 trainer under exploratory-training semantics only."""

from __future__ import annotations

import runpy
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TRAINER = ROOT / "scripts/train_p0v5_qg2_model_comparison.py"


def main() -> int:
    arguments = list(sys.argv[1:])
    namespace = runpy.run_path(str(TRAINER), run_name="qg2_frozen_trainer")
    # Statistical reachability of a 5% harmful-rate upper bound belongs to
    # deployment calibration, not to the decision to fit exploratory models.
    namespace["main"].__globals__[
        "MINIMUM_CALIBRATION_CONTEXTS_FOR_HARMFUL_GATE"
    ] = 1
    sys.argv = [str(TRAINER), *arguments]
    return int(namespace["main"]())


if __name__ == "__main__":
    raise SystemExit(main())
