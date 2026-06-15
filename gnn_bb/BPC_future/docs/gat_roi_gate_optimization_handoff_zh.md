# GAT Trajectory ROI Gate 优化交接文档

日期：2026-06-15

## 一句话主线

当前主线不是继续让 Pulse / worker 盲目找更多 true-RC negative 列，而是训练 GAT 判断“哪些负列更可能改善后续 RMP trajectory”，再由 kNN/OOD 安全壳决定 HIGH_PRIORITY 或 DELAY_QUEUE。

核心原则：

- GAT 负责 embedding / trajectory impact 表达；
- kNN/OOD 负责安全壳；
- 通过安全壳的负列可 HIGH_PRIORITY；
- 未通过安全壳的负列必须进入 DELAY_QUEUE；
- 任何 true-RC negative 列不能被永久丢弃；
- GAT / kNN / OOD 都不能参与 certificate 或 official lower bound。

## 最终目标

保证 exactness 不变的前提下，减少 20 规模以上实例的 CG 拖尾：

- 5/10 规模不能退化；
- 20 规模希望显著减少 TIME_LIMIT、tail retry、legacy final judge 开销；
- 目标不是“找到更多负列”，而是“加入能改善下一轮 RMP objective / retry / tail trajectory 的列”。

## 当前判断

已经确认几件事：

1. `true-RC negative != useful`
2. `add column != convergence`
3. `active support changed != positive ROI`
4. 只按 reduced cost 或 active/replacement proxy 采样，会产生大量无效样本。
5. 标签必须来自 worker 注入后的 trajectory 后效，而不是来自 RC、GAT 分数、kNN/OOD 决策或最终粗粒度状态。

当前更可靠的标签口径是 strict trajectory ROI：

- worker 确实注入目标列；
- 不产生 certificate / official bound side effect；
- 目标列进入 active support 或改变 active support；
- 注入后一轮 RMP objective 相对 baseline 同迭代不变差；
- 后续至少体现 wall time / exact call / retry / pricing tail / objective 等方向的改善。

如果 worker 自己下一轮 objective 下降，但相对 baseline 同迭代更差，必须标 negative。

## 当前数据与模型状态

最新可用 GAT 训练集：

- `BPC_future/data/gat_worker_roi/v36_v35_plus_active_replacement_partial3_hard_negative_20260615`
- 样本数：207
- 标签：`add=60`，`abstain=147`

最新训练结果：

- `BPC_future/results/gat_worker_roi_training_v36_focal_hard_20260615/summary.json`
- checkpoint：
  `BPC_future/results/gat_worker_roi_training_v36_focal_hard_20260615/gat_worker_roi_focal_hard.pt`
- validation：
  - precision 约 `0.405`
  - recall 约 `0.882`
  - 不能直接 production，需要 kNN/OOD 安全壳。

最新 kNN/OOD audit：

- calibrated：
  `BPC_future/results/gat_worker_roi_knn_ood_audit_v36_focal_hard_strict_targets_20260615/summary.json`
  - accepted batch count = 2
  - accepted batch ROI = 0.5
  - false-safe union 约 1.92%
  - label unsafe false-safe 约 2.78%
  - 仍不 production ready。
- zero-fp：
  `BPC_future/results/gat_worker_roi_knn_ood_audit_v36_focal_hard_zero_fp_20260615/summary.json`
  - false-safe = 0
  - accepted batch count = 0
  - 安全但无加速意义。

OOD/kNN 指标必须单独看，不能用普通 F1 代替：

- `safe_precision`
- `false_safe_rate_ood`
- `false_safe_rate_knn_unsafe`
- `false_safe_rate_label_unsafe`
- `false_safe_rate_union`
- `coverage`
- `delay_rate`
- `accepted_batch_count`
- `accepted_batch_roi`

目标阈值：

- false-safe rate 最好 `<= 1% ~ 2%`
- 实验上限 `<= 5%`
- coverage 不能过低，否则模型只是把大多数样本 delay，没有加速价值。

## v36 真实 20 A/B 关键发现

runbook：

- `BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/summary.json`
- candidate groups = 9
- input candidates = 24
- worker batch size = 4
- worker 固定为 target materialization worker，不允许 Pulse 搜索。

已完成的 partial5 post-injection audit：

- 报告：
  `BPC_future/logical_graph/run_reports/20260615_bpc_future_gat_active_replacement_v36_partial5_post_injection_zh.md`

关键结果：

- completed record count = 5
- target injection success = 5
- target returned journeys sum = 14
- target active changed task-set sum = 5
- target inactive changed task-set sum = 9
- final coarse positive ROI = 4
- strict trajectory positive = 0
- strict trajectory negative = 5
- immediate vs baseline same-iter improved count = 0
- worker next objective vs baseline same-iter delta sum = `+166.43642`

解释：

这些候选确实能注入 true-RC negative 列，也能改变 active support，但相对 baseline 同迭代 trajectory 更差。因此它们不能作为正 ROI 样本。

这也是为什么当前 `add_recall` 或 HIGH_PRIORITY 看起来不稳定：过去的候选“看起来像正样本”，但严格 trajectory 标签下其实是负样本。

## Worker 方法必须固定

后续做 GAT A/B 时，worker 必须固定，否则模型差异和 worker 差异会混在一起。

当前固定 worker 定义：

- fixed target materialization worker；
- 只物化 runbook 中指定的 target sequence / arc options / journey traces；
- 不允许 Pulse 搜索；
- 不允许 archive / pruning / adaptive sharding / fallback；
- 不允许 certificate effect；
- 只通过正常 add-column path 加入 RMP；
- target materialization 缺失时不能伪造候选。

不能把 worker 换成“更强搜索器”后再说 GAT 有效果。那测到的是 worker search ROI，不是 GAT ranking ROI。

## 不要再犯的错误

不要把下面这些当正标签：

- `rc < 0`
- `best_rc 很负`
- `worker_returned_journeys > 0`
- `active support changed`
- `final wall time 偶然下降`
- `final coarse ROI positive`
- `GAT 分数高`
- `kNN/OOD 通过`

它们都只能是候选信号，不是 trajectory ROI 标签。

真正标签必须回答：

这个候选被固定 worker 注入后，是否让下一轮或短 horizon 的 RMP trajectory 比 baseline 更好？

至少要比较：

- same-iteration baseline objective；
- worker next RMP objective；
- worker next dual L1 delta；
- follow-up pricing / exact / completion retry；
- active support 是否真改变；
- context hash 是否快速漂移；
- official status / primal / dual bound 是否不被 audit 改坏。

## 当前已补的测试保护

最近新增了 OOD/kNN 安全壳指标语义测试：

- `BPC_future/tests/test_gat_worker_roi_knn_ood.py`
- `BPC_future/tests/test_gat_same_run_batch_impact_knn_ood.py`

验证命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_gat_worker_roi_knn_ood \
BPC_future.tests.test_gat_same_run_batch_impact_knn_ood
```

已通过：

```text
test_gat_worker_roi_knn_ood: Ran 4 tests OK
test_gat_same_run_batch_impact_knn_ood: Ran 3 tests OK
```

## 下一步建议

### Step 1：先不要继续盲目采样

先把当前 v36 partial5 hard negatives 合入训练集，再重新训练/审计一次。

注意：partial5 包含 partial3，不要重复合并 partial3。

建议命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/build_gat_worker_roi_graph_dataset.py \
--input-jsonl BPC_future/results/gat_worker_roi_dataset_v36_active_replacement_partial5_hard_negative_20260615/gat_worker_roi_rows.jsonl \
--output-dir BPC_future/data/gat_worker_roi/v36_active_replacement_partial5_hard_negative_20260615 \
--report BPC_future/logical_graph/run_reports/20260615_bpc_future_gat_worker_roi_graph_dataset_v36_active_replacement_partial5_hard_negative_zh.md
```

这个数据集全是 hard negative，脚本可能返回非 0，但只要文件写出即可。

然后 merge：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/merge_gat_worker_roi_graph_datasets.py \
--input-dataset BPC_future/data/gat_worker_roi/v35_v34_plus_post_injection_hard_negative_20260615 \
--input-dataset BPC_future/data/gat_worker_roi/v36_active_replacement_partial5_hard_negative_20260615 \
--output-dir BPC_future/data/gat_worker_roi/v36_v35_plus_active_replacement_partial5_hard_negative_20260615 \
--report BPC_future/logical_graph/run_reports/20260615_bpc_future_gat_worker_roi_graph_dataset_v36_v35_plus_active_replacement_partial5_zh.md
```

### Step 2：同一数据集上训练 2-3 个无增量变体

不要改标签，不要换 worker，不要换 A/B 实例。

建议变体：

1. weighted BCE / focal loss：降低正样本被 DELAY_QUEUE 的概率；
2. hard-negative mining：提高 false HIGH_PRIORITY 负样本权重；
3. hard-positive mining：提高 false DELAY_QUEUE 正样本权重；
4. pairwise / ranking：同一 context 内学习“哪个候选更值得 HIGH_PRIORITY”；
5. family / scale 分组校准 kNN/OOD 阈值，不使用单一全局壳。

### Step 3：固定同一套真实 20 A/B

先跑已经求过最优或至少 baseline 行为清楚的 20 规模实例。

固定：

- 同一 instance；
- 同一 time limit；
- 同一 worker；
- 同一 target materialization；
- 同一 runbook；
- 只替换 GAT checkpoint / threshold / kNN-OOD shell。

比较：

- baseline；
- v36 focal-hard calibrated；
- v36 focal-hard zero-fp；
- 新 weighted / focal / pairwise 变体。

### Step 4：报告必须解释没有加速的原因

如果没有加速，需要区分：

1. 模型没有接受样本：
   - accepted batch count = 0
   - coverage 或 safe precision 问题
   - 原因偏 kNN/OOD 太保守
2. 接受了样本但不改善：
   - accepted batch ROI 低
   - same-iter objective 变差
   - 原因偏标签/候选机制问题
3. 接受样本且改善短 horizon，但最终不加速：
   - follow-up exact/retry 不降
   - 原因偏系统拖尾机制或 horizon 不够
4. 训练集不够：
   - scale/family 覆盖不足
   - positive ROI 太集中
   - OOD false-safe / coverage 无法同时满足

## 当前最可能的瓶颈

目前更像是候选机制和标签密度问题，不是单纯模型容量问题。

理由：

- active-replacement 候选能注入负列；
- 能改变 active support；
- 但 strict trajectory label 全负；
- 说明 proxy 选到的是“看起来像影响 RMP、实际同迭代更差”的候选。

所以不能只继续调 GAT。要检查正样本来自哪些 context / family / scale，再反推候选生成策略。

## 建议新窗口先做的最小任务

1. 读取本交接文档；
2. 查看 v36 partial5 post-injection report；
3. 合入 partial5 hard negatives；
4. 训练 2-3 个无增量数据变体；
5. 跑同一套 20 A/B；
6. 输出报告，必须包括：
   - OOD false-safe rate；
   - coverage；
   - delay rate；
   - accepted batch count；
   - accepted batch ROI；
   - same-iter objective delta vs baseline；
   - exact/pricing/retry delta；
   - 是否有真实 wall-time ROI。

## 生产化标准

不能只看单次 20 跑快了。至少要满足：

- 5/10 no-regression；
- 20 规模 hard-tail 上有稳定 ROI；
- accepted batch count > 0；
- accepted batch ROI 明显高于随机/旧策略；
- false-safe rate 最好 <= 1%~2%，最多 <= 5%；
- coverage 不能过低；
- DELAY_QUEUE 中负列仍 eventually reachable；
- 所有列通过 normal add-column path；
- 无 certificate / official lower-bound side effect；
- 同一模型在不同 family / scale 不出现明显安全壳失效。

未满足这些之前，GAT/kNN/OOD 只能 audit-only 或 strict experimental opt-in，不能默认启用。

