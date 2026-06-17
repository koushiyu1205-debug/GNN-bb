# GAT Target Mode：有针对性增加训练样本计划（2000 样本）

版本：2026-06-17  
目标阶段：Stage 3 → Stage 4 候选  
备注：本文件仅给执行计划，不改代码。

## 1) 目标与原则

本次目标是在不改变 exact-safe 边界的前提下，用 2000 个高质量样本解当前 Stage 3 的结构性瓶颈。核心原则如下：

1. 数据目标是 `same-context trajectory impact`，不是单点分类记忆。
2. 主指标不改变：`precision + accepted ROI + tail 风险` 联合达标才可进下一 stage。
3. 采样必须优先覆盖已知 `missed high-ROI` 区域；不能靠无区分度样本堆量。
4. 样本粒度默认改为 **individual target-level**，并补齐可用于 replay 的 kNN/OOD audit 字段。
5. 任务规模纳入 `20/30/50/100` 四档，不再偏重单一规模。

## 2) 当前阻塞对应的采样设计原则

先前 v107/ v99~v103 的失败主要是：

- 同 context 下 `high ROI` 与 `已放行低 ROI` 的排序冲突（rank failure）。
- context-batch 粗粒度标签误伤同 context 内正向子目标。
- family 覆盖与规模平衡不足（尤其 50/100 与部分 family）。
- kNN/OOD audit 不完整导致 Stage 4 边界无法通过。

因此新增样本要围绕这 4 点直接采样，不做“平均撒点”：

- **优先 hard pair**：同 context 内高 ROI 与低/负 ROI 对比；
- **先粒度后规模**：先做 individual target 级别，再按任务规模分布；
- **先问题再补全**：先补 missed 和 false-safe 场景，再补正样本；
- **先审计字段后模型**：每条样本都能回填 knn/ood 诊断。

## 3) 2000 样本目标分解（硬配额）

### 3.1 按任务规模（四档）

| 任务规模 | 目标样本数 | 占比 |
|---|---:|---:|
| 20 | 900 | 45% |
| 30 | 300 | 15% |
| 50 | 500 | 25% |
| 100 | 300 | 15% |
| **合计** | **2000** | **100%** |

### 3.2 按 family（阶段内目标）

| family | 目标样本数 | 备注 |
|---|---:|---|
| sector-wave | 900 | 继续保留主力覆盖，但不再单独主导 |
| random-wave | 700 | 扩大覆盖到高难 context |
| greedy-anchor | 400 | 强制补齐以防“家族空洞” |

### 3.3 按样本类型（训练作用）

| 样本类型 | 目标样本数 | 目的 |
|---|---:|---|
| same-context hard pair（missed） | 900 | 纠正排序/结构性失误 |
| positive trajectory gain（individual target） | 500 | 建立正向信号 |
| hard-negative / false-delay 对照 | 500 | 压制 unsafe 与 delay |
| 补全/边界样本（OOD/knn near boundary） | 100 | 提升稳定性与边界泛化 |

> 注：以上是目标配比框架，最终应以“去重 + 通过 causal reachability 审核后的有效样本”为准，允许小幅偏移（±5%）。

## 4) 样本定义（统一标准，先行冻结）

每条新增样本统一为 `individual target-level 行记录`，字段含义最小可包括：

1. `context_hash`, `instance`, `family`, `task_count`
2. `candidate_batch_id`, `target_id`
3. `trajectory_outcome`
   - `primal_roi`
   - `retry_roi`
   - `bad_mode_switch`
   - `accepted_impact_delta`（可选）
4. `same_context_pair_group`（可选，做 pair 对照时使用）
5. `label_group`
   - `high_roi_positive`
   - `false_delay_risk`
   - `hard_negative`
6. `kNN/OOD audit fields`（见 5）
7. `causal evidence id`（可重放脚本 hash + replay 证据文件）

禁止把 context-level 一个标签直接映射给所有 target。  
同一 context 下，如果有 positive/negative 子目标并存，必须拆为两条或多条 target-level 行。

## 5) kNN/OOD audit 同步字段（最小闭环）

每条新样本必须附带至少以下字段，且不允许缺省：

- `knn_k`
- `knn_max_neighbor_delay_fraction`
- `knn_candidate_delay_count`
- `knn_candidate_count`
- `knn_neighbor_delay_rate`
- `knn_in_distribution`
- `knn_safe_radius`
- `knn_safe_radius_multiplier`
- `knn_nearest_safe_distance`
- `ood_distance`
- `safe_distance_margin_ratio`
- `candidate_delay_risk_score`
- `candidate_delay_risk_threshold_used`
- `candidate_delay_gate_blocked`（true/false）
- `fallback_to_delay_queue`（true/false）

如果字段缺失或不可用，默认该样本不参与 Stage 3 门禁指标（避免污染 accepted/precision 统计）。

## 6) 数据产生方案（不改代码前提下）

### 阶段 A：现有证据挖掘（先补 hard pair）

1. 全量读取现有 Stage 3 相关报告：
   - v105/v106/v107
   - v98~v104 focused pair/contrast
   - v53 individual follow-up
2. 直接抽取已有 `missed` / `false_safe` / `false_delay` 行并重组为 target-level。
3. 设定每个 context 最少 1~2 个 hard pair 目标（有高 ROI 与低 ROI/负 ROI 对照）。

### 阶段 B：同 context 局部再试验（目标级标注）

1. 对每个高价值 context 做 targeted replay（不改运行策略，仅生成候选证据）：
   - 同一 context 内多条 target-level intervention；
   - 固定 dual/branch/cut 环境下做前后对比；
   - 捕获每个 target 的具体 outcome（trajectory ROI、retry/delay 与 bad-mode）。
2. 对 positive 与 negative 子目标分离标注，避免 context 池污染。

### 阶段 C：规模补齐（20/30/50/100）

1. 优先向 30/50/100 迁移补齐，但每个新增 context 先从 20 建立完整链路（可复现）再扩展到 30/50/100；
2. 在每个 family 内保证四档都有来源，规模与 family 交叉抽样，减少“同源偏置”。

### 阶段 D：family 任务空间平衡修正

1. 先把 `sector-wave` 的比例从“单一来源”改到 45%；
2. 对 `random-wave` 增加 high-variance 场景；
3. 对 `greedy-anchor` 强制保底 400 条，以免 holdout family collapse。

### 阶段 E：去重与一致性收口

1. 同 `context_hash + target_id + intervention_signature` 做主键去重。
2. 过滤无法复现/无 causal evidence 的记录。
3. 统一 label 口径（high-ROI 与 retry/primal 的口径一致）。

## 7) 采样规则（执行顺序）

1. 先满足 hard pair（先级 1）
2. 再补 positive trajectory 样本（先级 2）
3. 再补 hard-negative/false-delay（先级 3）
4. 最后补 OOD 边界样本（先级 4）

每个阶段达到配额后再进入下一阶段；任何阶段出现某 family/规模长期短缺，则先补齐短缺，再补其他。

## 8) 质量阈值与验收（进入下一次训练前）

### 8.1 数据硬门禁

- 同 context 的 positive/negative 成对样本比例 `< 0` 不允许（即不存在单侧标签上下文）。
- 4 档任务规模各自可用样本不低于目标的 80%（允许短缺但不低于 240/150/400/240）。
- 每个 family 至少 300 条且单 family 高 ROI 与 negative 子集都要存在。
- 每条样本具备 knn/ood 审计字段，否则剔除。

### 8.2 统计门禁（复用既有 Stage 3 指标）

- `admission pair pass rate` 与 `delay risk pair pass rate` 不低于上次基线的最高水平；
- `false-safe` 与 `false-high-priority on delay` 不能回升；
- `family_holdout_min_accepted_roi` 不允许在同一 family 明显掉落；
- `precision/accepted batch ROI` 可用样本覆盖后仍可报出置信下界。

## 9) 里程碑（按两周节奏）

1. **第 1 周：清单和归档**
   - 完成 v107 前置信号 context 清单；
   - 完成现有 logs 的 target-level 重写；
   - 输出第一版 `2000` 采样追踪表。
2. **第 2 周：补齐与闭环**
   - 按配额完成 20/30/50/100、family、类型目标；
   - 完成 knn/ood 字段补齐；
   - 产出 `final_sample_manifest.json` 与 `pair_index.json`；
   - 输出“可训练版本 + 被剔除版本”对照。
3. **第 3 周（可选）: 预备训练集重算**
   - 仅在计划内不改代码的前提下，交付最少三种抽样切片（A/B/C）供下轮训练验证。

## 10) 风险与防过拟合措施

- 风险 1：过度聚焦 miss 场景导致泛化损失。  
  - 缓解：保留 30% 非 miss 样本做泛化锚点。
- 风险 2：规模偏斜导致 20-task 表现看好、50/100 退化。  
  - 缓解：严格保留四档配额，并按规模独立看 holdout。
- 风险 3：kNN/OOD 字段难补齐。  
  - 缓解：无法补齐则标记 `audit_missing=true` 并排除入训练主指标。
- 风险 4：target-level 重写错误复用 context 标签。  
  - 缓解：同 context 内 positive/negative 子目标必须独立列，并通过 replay evidence 校验。

## 11) 交付清单

1. `stage3_targeted_sample_plan_manifest_v107.json`  
2. `stage3_targeted_sample_rows_v107.jsonl`（2000 行）  
3. `stage3_targeted_sample_pair_index_v107.jsonl`（same-context hard pair 索引）  
4. `stage3_targeted_sample_knn_ood_audit_v107.jsonl`（字段闭环核对）  
5. `sample_allocation_report_v107.md`（按 family / 任务规模 / family×规模 / 类型分布）

---

## 结论

这个计划不是“加更多数据”而是“加对数据”。  
核心成功条件是：在保持安全边界不放松的前提下，通过 targeted、可回放、individual target 级样本把
`v107 这类 rank failure` 从“结构性盲区”转为“可学习约束”，并把 20/30/50/100 四档同时进入训练与 holdout，最终把 Stage 4 的 gate 从配额卡点变成可通过状态。
