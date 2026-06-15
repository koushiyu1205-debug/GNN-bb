# GAT Positive ROI Mining Candidates v28 报告

日期：2026-06-15

## 目的

从已有未标注候选池中优先选择非 random、高正率 cell 的 task20 候选，用真实 worker A/B 采集 trajectory ROI 标签。

## 机器字段

```json
{
  "all_non_random": true,
  "all_task20": true,
  "available_unlabeled_non_random_candidate_count": 66,
  "candidate_count": 16,
  "candidate_family_region_counts": {
    "greedy-anchor|apollo15_20km": 4,
    "greedy-anchor|tranquillitatis_balmer_like_20km": 4,
    "sector-wave|apollo15_20km": 4,
    "sector-wave|tranquillitatis_balmer_like_20km": 4
  },
  "certificate_ready": false,
  "decision_counts": {
    "DELAY_QUEUE": 6,
    "HIGH_PRIORITY": 10
  },
  "impact_bucket_counts": {
    "": 1,
    "new_support_changing": 14,
    "new_task_set": 1
  },
  "production_ready": false,
  "schema_version": "gat_positive_roi_mining_candidates_v28",
  "selected_candidates": [
    {
      "cell_positive_rate": 0.4,
      "decision_name": "DELAY_QUEUE",
      "impact": "new_support_changing",
      "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json",
      "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_e8e35421df342768_5_14_1_20",
      "ordinal_positive_rate": 1.0,
      "score": 13.851324,
      "target_sequence": [
        5,
        14,
        1,
        20
      ]
    },
    {
      "cell_positive_rate": 0.269231,
      "decision_name": "DELAY_QUEUE",
      "impact": "new_support_changing",
      "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_04_seed61306_logical_graph.json",
      "name": "apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b6507dfb6db81d64_16_11_12_10",
      "ordinal_positive_rate": 1.0,
      "score": 13.834605,
      "target_sequence": [
        16,
        11,
        12,
        10
      ]
    },
    {
      "cell_positive_rate": 0.4,
      "decision_name": "DELAY_QUEUE",
      "impact": "new_support_changing",
      "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json",
      "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_126440b08b9f25f5_5_18_10_14_1_20",
      "ordinal_positive_rate": 1.0,
      "score": 13.832733,
      "target_sequence": [
        5,
        18,
        10,
        14,
        1,
        20
      ]
    },
    {
      "cell_positive_rate": 0.4,
      "decision_name": "HIGH_PRIORITY",
      "impact": "new_support_changing",
      "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json",
      "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_20_18_3_4",
      "ordinal_positive_rate": 1.0,
      "score": 13.826739,
      "target_sequence": [
        20,
        18,
        3,
        4
      ]
    },
    {
      "cell_positive_rate": 0.4,
      "decision_name": "HIGH_PRIORITY",
      "impact": "new_task_set",
      "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json",
      "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_10_1_16_7_17_4",
      "ordinal_positive_rate": 1.0,
      "score": 12.221422,
      "target_sequence": [
        10,
        1,
        16,
        7,
        17,
        4
      ]
    },
    {
      "cell_positive_rate": 0.36,
      "decision_name": "HIGH_PRIORITY",
      "impact": null,
      "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json",
      "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_13_8_11",
      "ordinal_positive_rate": 0.75,
      "score": 11.815615,
      "target_sequence": [
        13,
        8,
        11
      ]
    },
    {
      "cell_positive_rate": 0.347826,
      "decision_name": "HIGH_PRIORITY",
      "impact": "new_support_changing",
      "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json",
      "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_bec78bfc0baddb44_6_11_2",
      "ordinal_positive_rate": 0.0,
      "score": 10.86711,
      "target_sequence": [
        6,
        11,
        2
      ]
    },
    {
      "cell_positive_rate": 0.36,
      "decision_name": "HIGH_PRIORITY",
      "impact": "new_support_changing",
      "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json",
      "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_587e2ac350a8619b_15_6_11_12_14",
      "ordinal_positive_rate": 0.5,
      "score": 10.775807,
      "target_sequence": [
        15,
        6,
        11,
        12,
        14
      ]
    },
    {
      "cell_positive_rate": 0.347826,
      "decision_name": "HIGH_PRIORITY",
      "impact": "new_support_changing",
      "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json",
      "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_0f0c5d214add6400_20_18_2_1_19",
      "ordinal_positive_rate": 0.0,
      "score": 10.585951,
      "target_sequence": [
        20,
        18,
        2,
        1,
        19
      ]
    },
    {
      "cell_positive_rate": 0.347826,
      "decision_name": "DELAY_QUEUE",
      "impact": "new_support_changing",
      "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json",
      "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_03_seed61206_d1096c4029531f56_7_1_8_11_19",
      "ordinal_positive_rate": 0.0,
      "score": 10.522313,
      "target_sequence": [
        7,
        1,
        8,
        11,
        19
      ]
    },
    {
      "cell_positive_rate": 0.347826,
      "decision_name": "DELAY_QUEUE",
      "impact": "new_support_changing",
      "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json",
      "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_1b98b5f990279d7b_13_1_16_8",
      "ordinal_positive_rate": 0.0,
      "score": 10.447985,
      "target_sequence": [
        13,
        1,
        16,
        8
      ]
    },
    {
      "cell_positive_rate": 0.269231,
      "decision_name": "HIGH_PRIORITY",
      "impact": "new_support_changing",
      "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json",
      "name": "apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_3a9af4966d4b91d5_8_15_12_9",
      "ordinal_positive_rate": 0.25,
      "score": 9.750955,
      "target_sequence": [
        8,
        15,
        12,
        9
      ]
    },
    {
      "cell_positive_rate": 0.36,
      "decision_name": "HIGH_PRIORITY",
      "impact": "new_support_changing",
      "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json",
      "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_ea2f1344458c548f_6_14_3_4_18",
      "ordinal_positive_rate": 0.166667,
      "score": 9.384511,
      "target_sequence": [
        6,
        14,
        3,
        4,
        18
      ]
    },
    {
      "cell_positive_rate": 0.36,
      "decision_name": "HIGH_PRIORITY",
      "impact": "new_support_changing",
      "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json",
      "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_5_4_16_18",
      "ordinal_positive_rate": 0.166667,
      "score": 9.170424,
      "target_sequence": [
        6,
        5,
        4,
        16,
        18
      ]
    },
    {
      "cell_positive_rate": 0.269231,
      "decision_name": "HIGH_PRIORITY",
      "impact": "new_support_changing",
      "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json",
      "name": "apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_1fa17aea2063098d_4_12_15_6_11",
      "ordinal_positive_rate": 0.0,
      "score": 8.883507,
      "target_sequence": [
        4,
        12,
        15,
        6,
        11
      ]
    },
    {
      "cell_positive_rate": 0.269231,
      "decision_name": "DELAY_QUEUE",
      "impact": "new_support_changing",
      "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612_logical_graph.json",
      "name": "apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_8b4a2367b0350bfe_4_18_6",
      "ordinal_positive_rate": 0.0,
      "score": 8.750609,
      "target_sequence": [
        4,
        18,
        6
      ]
    }
  ],
  "source_candidate_file_count": 48,
  "training_label_requires_worker_ab": true
}
```

## 结论

- 这些候选仍不是训练标签，必须经过 worker A/B audit 后才能进入 GAT ROI 训练集。
- 选择策略只影响采样顺序，不参与证书，不默认启用 production。
