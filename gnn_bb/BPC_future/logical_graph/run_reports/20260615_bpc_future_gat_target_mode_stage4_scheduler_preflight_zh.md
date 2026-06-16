# 2026-06-15 BPC_future GAT Target Mode Stage 4 Scheduler Preflight 报告

## 结论

本轮开始 Stage 4 的最小安全前置，但没有接入 solver 主路径，也没有运行
shadow / opt-in online A/B。

新增的是 default-off、纯 Python 的 admission queue 语义层，用来固定以下 exact-safe
合同：

- true-RC negative 只能是 `HIGH_PRIORITY` 或 `DELAY_QUEUE`；
- true-RC nonnegative 才能是 `REJECT_NONNEGATIVE_ONLY`；
- `DELAY_QUEUE` 不是 discard；
- 超过 finite-delay 或 queue capacity 时，候选必须 due for release / re-expose；
- certificate 前，所有 delayed candidates 必须 re-expose；
- selector / queue 永远不能产生 certificate；
- final certificate 仍必须来自 exact pricing full scan。

## 新增文件

- `BPC_future/solver/gat_admission_queue.py`
  - `GATAdmissionCandidate`
  - `GATAdmissionDecision`
  - `GATDelayQueueEntry`
  - `GATCertificatePreflight`
  - `GATAdmissionQueue`

- `BPC_future/tests/test_gat_target_mode_scheduler.py`
  - 覆盖 negative 不会被 reject；
  - 覆盖 finite-delay release；
  - 覆盖 queue capacity pressure 只触发 release，不会静默丢弃。

- `BPC_future/tests/test_gat_target_mode_certificate_safety.py`
  - 覆盖 delayed current negative 会阻止 learned certificate preflight；
  - 覆盖 delayed candidate 变 nonnegative 后 selector 仍不能 certificate；
  - 覆盖 certificate 前所有 delayed candidates 都 due for re-exposure。

## 边界

本次没有修改：

- `manual_journey_reduced_cost()`；
- `JourneyPricingResult` / `CERTIFIED_NO_NEGATIVE` 判定；
- `journey_driver.py` 主循环；
- `journey_pricing.py` dispatch / final judge；
- benchmark 默认配置。

因此当前 Stage 4 preflight 只证明 scheduler/certificate safety 的单元语义，不证明
5/10 no-regression、20-task ROI 或 20-task 200 秒 exact target。

## 验证

已运行：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest BPC_future.tests.test_gat_target_mode_scheduler BPC_future.tests.test_gat_target_mode_certificate_safety BPC_future.tests.test_gat_batch_impact_training BPC_future.tests.test_gat_batch_impact_knn_ood BPC_future.tests.test_learning_components.ContextAwareColumnSelectorTests
```

结果：

```text
Ran 14 tests in 0.189s
OK
```

## 下一步

Stage 4 的下一步仍必须保持 default-off：

1. 增加 shadow-mode logging hook，记录如果启用 GAT 会怎样调度，但不改变 solver decision；
2. 对 5/10 跑 shadow no-regression；
3. 通过后才允许 20-task opt-in A/B；
4. certificate mode 中必须继续关闭 GAT hard filter，并在 final proof 前 re-expose delayed negative。
