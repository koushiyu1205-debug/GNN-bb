"""中文摘要：根目录 clean BPC 包。这里实现独立的 Branch-Price-and-Cut 主线，不依赖旧 bp 实验入口。"""

from .solver import BPCResult, solve_bpc_clean

__all__ = ["BPCResult", "solve_bpc_clean"]
