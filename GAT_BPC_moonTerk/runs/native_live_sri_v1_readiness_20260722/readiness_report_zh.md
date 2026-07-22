# Native Live SRI V1 Readiness 诊断报告

本报告只读取冻结 no-cut BPC 树中的 RMP primal snapshot；不添加 cut、不重求解 RMP，
因此不会改变任何正式 lower bound 或 exact certificate。

## 20 规模

- root：9/20 存在 violated SRI；最大 violation=0.500000001。
- fractional branch：40/40 存在 violated SRI，比例=100.00%。

## 30 规模

- root：15/20 存在 violated SRI；最大 violation=0.5。
- fractional branch：156/156 存在 violated SRI，比例=100.00%。

## 决策

- 稳定 SRI signal：True。
- P2 branch gate：True（branch violation rate=100.00%）。
- 建议：`RUN_P0_P1_ROOT_ONLY_PILOT`。

受冻结 JSON 内容限制，restricted-RMP bound movement 在本轮不可重建；该指标必须由后续 fresh P0/P1 root-only pilot 在完整 JourneyColumn 状态上测量。
