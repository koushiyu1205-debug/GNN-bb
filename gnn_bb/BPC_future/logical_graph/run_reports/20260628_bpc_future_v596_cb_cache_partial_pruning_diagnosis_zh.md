# 20260628 V596 completion-bound next-sortie cache 与 partial pruning 诊断

## 结论

本轮推进的是上一份 retry gate 诊断后的下一步：检查 `completion-bound / final-judge` 单次证明成本，尤其是为什么打开

```text
journey_certificate_completion_bound_next_sortie_cache_enabled=True
```

后，日志里 `direct_next_sortie_cache_hits/misses` 仍为 0。

结论：

1. cache 不是坏的；在 `direct_journey_label_completion_bound_partial_pruning_enabled=False` 时，它确实会产生大量 hit/miss。
2. 默认 certificate path 中 `journey_certificate_completion_bound_partial_pruning_enabled=True`，核心 pricing 会把实际 `use_next_sortie_cache=False`，因为 partial pruning 依赖 parent-specific label state，不能用只按 used-mask 缓存的 sortie profile 混用。
3. 强行关闭 partial pruning 让 cache 生效后，两个 20-scale 高耗时实例仍然 600s 超时，而且 total profile generation time 从约 `580.233s` 上升到 `862.402s`。
4. 所以不能把“打开 next-sortie cache”当作当前加速主线。默认 partial pruning 比这个 cache 更关键。

## 代码改动

只做诊断增强，不改变求解、bound、certificate、branch 行为。

### `BPC_future/pricing/journey_pricing.py`

`JourneyPricingResult` 新增字段：

```text
direct_next_sortie_cache_requested
direct_next_sortie_cache_effective_enabled
direct_next_sortie_cache_disabled_reason
```

direct-label pricing 内部现在会区分：

- config 请求打开 cache；
- 实际是否启用 cache；
- 若请求打开但被关闭，记录关闭原因。

当前关键关闭原因：

```text
completion_bound_partial_pruning_enabled
```

### `BPC_future/solver/journey_driver.py`

pricing JSONL 事件新增同名字段：

```text
direct_next_sortie_cache_requested
direct_next_sortie_cache_effective_enabled
direct_next_sortie_cache_disabled_reason
```

这样后续日志不会再被 `direct_journey_label_next_sortie_cache_enabled=True` 误导；那个字段只是 config 状态，不代表实际 cache path 被使用。

### `BPC_future/scripts/audit_journey_completion_tail_profile.py`

completion-tail audit 新增聚合：

```text
completion_retry_cache_requested_count
completion_retry_cache_effective_count
completion_retry_cache_disabled_reason_counts
```

## 测试

通过：

```text
python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_direct_journey_label_completion_bound_can_keep_next_sortie_cache \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_direct_journey_label_completion_bound_reports_cache_disabled_by_partial_pruning
```

结果：

```text
Ran 2 tests in 0.030s
OK
```

retry gate 相关测试仍通过：

```text
python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_completion_bound_retry_gate_is_opt_in_and_requires_history \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_completion_bound_retry_gate_blocks_expensive_zero_harvest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_completion_bound_retry_gate_keeps_harvest_signal \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_completion_bound_retry_gate_context_scope_isolates_depth_trigger \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_completion_bound_retry_budget_cap_is_opt_in_and_contextual \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_completion_bound_retry_budget_cap_keeps_unseen_context_uncapped
```

结果：

```text
Ran 6 tests in 0.000s
OK
```

audit 脚本测试通过：

```text
python -m unittest BPC_future.tests.test_journey_completion_tail_profile
```

结果：

```text
Ran 2 tests in 0.002s
OK
```

## smoke 设置

新 smoke：

```text
BPC_future/results/20260628_retry_on_off_gate_smoke4_randomtw20/retry_on_cb_cache_partialoff_smoke2/
```

实例：

- seed61311：`tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04`
- seed61410：`tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05`

关键配置：

```text
journey_certificate_completion_bound_next_sortie_cache_enabled=True
journey_certificate_completion_bound_partial_pruning_enabled=False
```

同前一组保持：

- 600s 外部时限
- max-workers 2
- V545-like branch score
- early branch off
- admission off
- completion-bound/final-judge retry on

## smoke 结果

| group | instances | status | gap available | profile generation time | cache hits | cache misses |
|---|---:|---|---:|---:|---:|---:|
| cache on + partial pruning on | 2 | 2 EXTERNAL_TIME_LIMIT | 2/2 | 580.233s | 0 | 0 |
| cache on + partial pruning off | 2 | 2 EXTERNAL_TIME_LIMIT | 2/2 | 862.402s | 114642 | 14421 |

说明：

- `cache on + partial pruning on` 是旧日志，尚未包含 requested/effective 字段，但 hit/miss 为 0，结合代码可知实际 cache 被 partial pruning 关闭。
- `cache on + partial pruning off` 是新日志，`completion_retry_cache_requested_count=38`，`completion_retry_cache_effective_count=38`，说明 cache 真实生效。

单实例：

| instance | partial on profile | partial off profile | partial off cache | 结果 |
|---|---:|---:|---:|---|
| seed61311 | 262.884s | 443.647s | 49356 hit / 5864 miss | 更慢，仍超时 |
| seed61410 | 317.349s | 418.755s | 65286 hit / 8557 miss | 更慢，仍超时 |

partial-off 的求解结果：

| instance | status | wall | gap |
|---|---:|---:|---:|
| seed61311 | EXTERNAL_TIME_LIMIT | 600.028s | 0.046017 |
| seed61410 | EXTERNAL_TIME_LIMIT | 600.020s | 0.034203 |

## 解释

`next_sortie_cache` 缓存的是某个 used-mask 下的 sortie profile。它适合没有 parent-specific suffix pruning 的情形。

但 certificate completion-bound 默认启用 partial pruning。partial pruning 会基于当前 journey label 的：

- current value；
- sortie count；
- end time；
- suffix lower bound；
- cut reward / branch constraints；

直接剪掉大量 parent-specific 扩展。因此只按 used-mask 缓存 profile 会失去这些剪枝，导致：

- cache hit 很高；
- 但 evaluated timed trips 大幅增加；
- profile generation time 反而更高。

这次 partial-off 的总量就是证据：

```text
cache hits/misses = 114642 / 14421
generated sequences = 11,329,146
evaluated timed trips = 25,487,475
profile generation time = 862.402s
```

而 partial-on 同两个实例：

```text
generated sequences = 16,834,944
evaluated timed trips = 2,855,717
profile generation time = 580.233s
```

partial-on 虽然 generated sequences 更多，但 evaluated timed trips 少一个数量级，最终更快。

## 对主目标的影响

这次没有带来 20-scale OPTIMAL 改善；目标仍未完成。

但它排除了一个错误方向：

> 不能靠关闭 partial pruning 来换 next-sortie cache。

下一步主线应该是：

1. 保持 certificate partial pruning 默认开启。
2. 不把 `journey_certificate_completion_bound_next_sortie_cache_enabled=True` 作为默认优化。
3. 如果继续做 cache，只能研究更细粒度且 parent-aware 的 cache，例如 key 包含足够的 parent state 或只缓存安全的下界/可复用子结构，而不是缓存完整 next-sortie profile 后绕过 parent-specific pruning。
4. 更优先的是减少进入 certified final-judge 的节点数量：branch score 需要惩罚 `completion_bound_tail`、`child_completion_bound_retries`、`child_certificate_pricing_events` 和 right-censored proof tail。

## 后续建议

短期不改默认运行配置。

下一步更值得做的是 proof-tail-aware branch score overlay：

- 从已有 branch impact audit 中抽取 high `child_completion_bound_retries`、high `child_certificate_pricing_events`、right-censored `completion_bound_tail` 的 pair/context；
- 生成一个风险惩罚 overlay；
- 在 smoke4 或 full60 high-retry 子集上验证是否减少 completion-bound retry 总数；
- 验收不看单纯 wall time，必须看 OPTIMAL / gap_available / gap / completion-bound retry count。

这比继续调 cache 或 retry gate 更贴近当前瓶颈。
