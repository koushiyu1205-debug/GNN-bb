# P0V5 QG2 TinyGAT force-on 诊断

更新时间：2026-08-07；本文件记录 development-only 证据，不构成部署授权。

## 当前模型和边界

- 当前模型是 `QG2TinyGAT`：2层 edge-aware attention、hidden 32、2 heads、24,337参数；
- 每个 pricing request 只推理一次，Native 对每个 label 计算固定标量 priority；
- QG2只改变同一 reduced-cost bucket 内的队列顺序；
- 未改变合法扩展、dominance判定、bound、RC、label删除和certificate；
- P0V4/P0V5 Exact control与production均未切换。

## 已完成的 force-on context

前三个完整3重复 scale30 context：

| state | Q0 median (s) | TinyGAT median (s) | ratio | processed-label ratio |
|---|---:|---:|---:|---:|
| `098f8374d1680b19` | 4.174 | 5.392 | 1.292 | 1.317 |
| `0e222da795d14da2` | 2.273 | 2.615 | 1.150 | 1.154 |
| `0761d9c2343be849` | 0.358 | 0.526 | 1.468 | 1.460 |

当前 paired GM 为 `1.2969`，正收益 `0/3`。这些 context 全部达到相同
`EXACT_PROOF_COMPLETION`，安全审计一致。

重尾 context `1ceab640c7be1580` 的第1次重复：

| arm | status | wall (s) | processed labels | dominance candidate checks |
|---|---|---:|---:|---:|
| Q0 | COMPLETE | 278.956 | 7,795,188 | 15,333,054,857 |
| TinyGAT, bucket `1e-3` | TIMEOUT | 301.646 | 6,882,700 | 17,093,640,348 |

TinyGAT Native label scoring估计只占约`0.827 s`；退化不是推理开销，而是新顺序
产生了更昂贵的frontier/dominance轨迹。最终保留了两次完整Q0和三次TinyGAT结果：
Q0分别为`278.956 s`、`290.750 s`并完成证明；TinyGAT分别在`301.646 s`、
`301.663 s`和`301.780 s`超时。第三次Q0在用户确认停止后被终止，未伪造或写入完成结果。

## 动作面诊断

前三个完整context中，TinyGAT给所有scored labels非零priority，产生约15.8万、
158.6万和188.7万次ordering differences。重尾context第1次重复产生约3,073.8万次
ordering differences。`同bucket重排`在实现上仍是大范围动作，不是局部one-deviation。

相同current-engine snapshot的既有leaked-QO2结果进一步表明bucket敏感：

| state `1ceab...` | Q0 | QO2 `1e-4` | QO2 `3e-4` | QO2 `1e-3` |
|---|---:|---:|---:|---:|
| wall (s) | 278.807 | 258.050 | 252.663 | TIMEOUT 301.341 |

因此当前`1e-3`失败不能在数学上证明所有TinyGAT potential都无效，但已有证据足以说明
这版可部署候选明显退化。用户决定不再为窄bucket继续消耗求解时间；窄bucket runner仅保留
为development tooling，没有启动，不构成后续计划。

## 多臂证据

当前engine下33个scale30 proof contexts的既有单次matched参考结果：

| arm | matched | GM | beneficial |
|---|---:|---:|---:|
| QD1 | 33 | 0.8383 | 26 |
| QB1 | 26 | 1.3484 | 1 |
| leaked-QO2 `1e-4` | 32 | 0.9793 | 23 |
| leaked-QO2 `3e-4` | 32 | 0.9889 | 19 |
| leaked-QO2 `1e-3` | 31 | 0.9992 | 20 |

这些单次结果只能用于选择下一步，不代替3次blocked fresh-process验收。它们支持：

1. scale30 proof tail中QD1是必须保留的动作；
2. TinyGAT不应被强制用于所有fallback contexts；
3. 后续Context GAT的动作必须是`QG2/QD1/QB1`，所有动作被拒绝时严格回Q0；
4. scale50还缺少current-engine的QD1/QB1 matched outcomes，必须补采后才能训练正式selector。

## 终止决定

1. 当前force-on已按用户决定停止；未完成的scale30/scale50 context不再运行；
2. 当前TinyGAT checkpoint保持development-only，禁止部署和production切换；
3. 不启动窄bucket、QD1/QB1新采集、Context GAT、MLP或Linear；
4. P0V4/P0V5 Exact control保持原样；
5. 若以后另行选择multi-arm Context GAT，应作为新方向重新授权，不把本轮负结果包装成成功。
