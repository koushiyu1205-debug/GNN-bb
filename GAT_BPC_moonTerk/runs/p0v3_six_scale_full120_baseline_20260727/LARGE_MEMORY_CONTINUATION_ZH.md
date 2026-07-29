# P0 V3 scale50/100 大内存续跑说明

## 当前状态

- scale5/10/20/30：各20例，共80例 exact。
- scale50/001：8 GiB内存墙诊断，`LEGAL_INCOMPLETE`，必须在大内存
  环境重跑。
- scale50/002：人工暂停，不进入正式rows。
- scale50/003--020与scale100/001--020：尚未运行。
- 当前停止原因：`PAUSED_INSUFFICIENT_LARGE_SCALE_MEMORY`。

## 合格环境

续跑入口默认要求Linux可见总内存至少360 GiB，推荐380 GiB以上，对应
384 GB级计算节点。运行时按机器实际内存计算三层限制：

1. Native cooperative limit；
2. Native host emergency watchdog；
3. outer process-tree emergency cap。

Native限额取以下两者较小值并向下取整：

```text
0.875 * MemTotal
MemTotal - 48 GiB system reserve - 4 GiB watchdog/launcher reserve
```

这不会改变P0 V3求解器、数学模型、定价顺序或证书语义，只改变50/100的
资源包络。每个实例仍为严格冷启动、3600秒上限、串行执行。

## 迁移要求

大内存节点必须保留相同的仓库相对路径内容，至少包括：

- `src/`与`scripts/`；
- `configs/native_live_sri_p0_full120_v1.yaml`；
- `runs/frozen_native_live_sri_p0_no_task_wait_baseline_v3_20260725/`；
- 当前目录中的`full120_rows.json`及其80个small-scale结果；
- `data/instances/lunar_ice_sp50_050/`；
- `data/instances/lunar_ice_sp50_100/`；
- 正式实例manifest。

不要只复制summary；续跑预检会核验80个exact rows、冻结Native模块、
正式实例路径和当前baseline registry。

## 续跑命令

先只做资格检查和生成runtime config：

```bash
/home/kai/miniconda3/bin/python \
  scripts/prepare_p0v3_large_memory_continuation.py \
  --output-dir runs/p0v3_six_scale_full120_baseline_20260727
```

预检通过后直接执行：

```bash
/home/kai/miniconda3/bin/python \
  scripts/prepare_p0v3_large_memory_continuation.py \
  --output-dir runs/p0v3_six_scale_full120_baseline_20260727 \
  --execute
```

入口会保留5--30的80个exact rows和已经真正耗尽3600秒的合法time-limit
rows，只删除并重跑恢复到的`MEMORY_CENSORED_INCOMPLETE`、
`RESOURCE_CENSORED_INCOMPLETE`和`UNSAFE_FAILURE`大规模行。Ctrl-C会先
清理完整子进程组，不再遗留占用大内存的Native host。

## 完成判据

完成并不要求120例全部exact；3600秒安全耗尽是正式time-limit结果。必须
满足：

- 120个slot全部有终态行；
- `unsafe_failure_count = 0`；
- exact行证书和ledger全部通过；
- timeout行不得产生exact/no-negative证书；
- 任何`MEMORY_LIMIT`仍需单独报告，不能归并为time-limit；
- scale50/100不再出现8 GiB诊断配置。
