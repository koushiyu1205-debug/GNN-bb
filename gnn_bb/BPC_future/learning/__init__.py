"""Learning-side helpers for BPC_future.

The package intentionally avoids importing PyTorch at package import time.
Import concrete modules such as ``BPC_future.learning.gnn_model`` when the
learning dependencies are installed.
"""

__all__ = [
    "batch_impact_model",
    "branch_impact_model",
    "column_selector",
    "dual_stabilizer",
    "gnn_model",
    "graph_builder",
]
