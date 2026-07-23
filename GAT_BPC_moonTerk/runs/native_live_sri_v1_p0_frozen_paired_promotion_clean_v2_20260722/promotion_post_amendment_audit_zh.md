# Native Live SRI V1 Frozen Paired Promotion 后置审计

- 审计状态：`PASS`
- 正式行：`1040/1040`；raw acceptance summaries：`1040/1040`
- exact / zero-redline / no-cheat / certificate / engine-valid：`1040/1040/1040/1040/1040`
- objective 最大绝对差：`9.99999999918e-07`；新容差失败：`0`；旧容差误报：`3`
- RC mismatch / manual RC fail / certificate leak 总数：`0/0/0`
- 最大进程树 RSS：`4.163532 GiB`；最低 available memory：`8.565281 GiB`；最低磁盘余量：`818.004 GiB`

## Promotion 结论

- scale 5: correctness=`True`, performance=`True`, promotion=`True`, mean ratio=`1.003516`, p50 ratio=`0.999396`, paired geomean=`1.003480`, CI=`[0.996809, 1.009628]`
- scale 10: correctness=`True`, performance=`True`, promotion=`True`, mean ratio=`0.981068`, p50 ratio=`0.958215`, paired geomean=`0.979668`, CI=`[0.951791, 0.999489]`
- scale 20: correctness=`True`, performance=`True`, promotion=`True`, mean ratio=`0.805249`, p50 ratio=`0.793010`, paired geomean=`0.864355`, CI=`[0.771307, 0.951162]`
- scale 30: correctness=`True`, performance=`False`, promotion=`False`, mean ratio=`1.087746`, p50 ratio=`0.835094`, paired geomean=`0.959039`, CI=`[0.824718, 1.103403]`

最终：`NOT_PROMOTED`；不得切换默认主线。冻结 no-cut 继续作为 5/10/20/30 production default。
