# P0V5 Counterfactual-Prefix V8R1 证据修复说明

## 1. 修复边界

V8 原 run root 永久只读。其 `COUNTERFACTUAL_PREFIX_NOT_IDENTIFIABLE` 不能作为有效性能结论，原因不是 gate 被放宽，而是 gate 输入违反了冻结的测量语义：

- `total_fresh_process_wall_sec` 被误当作 warm prefix wall；
- 128、512、2048 三个预算均执行到 2048，因而使用同一总 wall；
- Native 未输出 checkpoint endpoint elapsed wall；
- action-previsible lifecycle 特征未绑定到 Native graph context；
- probes 发生后，reject/error 路径未必构造独立 formal exact Q0 request。

V8R1 只修复这些证据合同，不修改 boundary、checkpoint grid、图样本容量、GAT 架构、标签、threshold 或 acceptance gate。

## 2. Native 修复

- prefix telemetry 为 base 和每个 endpoint 输出 request elapsed、rollout elapsed、graph-build wall；
- `maximum_rollout_budget` 必须是 `128/512/2048` 之一，Native 在所选 checkpoint 立即结束 telemetry-only request；
- graph context 继承 Python 绑定的 active-column、round、dual-delta、midpoint-wall presence 特征；
- Q0/QD1 base graph hash、route/certificate suppression 和 `sizeof(State)==176` 合同保持不变；
- 旧 V7 binary 与 V8R1 binary 进行 500-case cross-binary Q0 differential。

## 3. 正确计时

Representation development 仍可在一次 2048 request 中取得三个 endpoint，但每个预算只使用对应 endpoint 的 Native `request_elapsed_wall_seconds`。cold fresh-process wall 单独保留为诊断字段，禁止进入 warm p99、2% fraction 或 taxed oracle。

正式 runtime 在两个 probes 后无论选择、拒绝还是 post-probe fail-closed，均创建独立 exact request。只有 probes 之前的 scale/lifecycle/manifest bypass 才返回同一原 request 对象。

## 4. 不可变链

新证据进入：

```text
runs/p0v5_counterfactual_prefix_gat_qd1_selector_v8r1_20260818/
```

该链冻结原 V8 terminal/report hash，并标记其性能 authority 为 false。V8R1 重新采集全部 38×2 prefix tasks；不得复用原 V8 prefix wall 或 graphs。若修复后的 cost gate 失败，写入新的合法 negative terminal；只有 cost gate 通过才允许运行 grouped-OOF representation gate。

## 5. 验证

- CTest：Native queue、prefix suppression、selected-budget stop、base hash、State size；
- Python：graph determinism、task permutation、pooling invariance、cut interaction、outcome leakage、100-triplet C++/PyTorch parity；
- Runtime：small/tree pre-manifest identity bypass，post-probe reject/error 的独立 exact Q0；
- 500-case old/new Q0 route、RC、certificate-field 和 pop-derived counter differential。
