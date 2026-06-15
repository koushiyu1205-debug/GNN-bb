# GAT Positive ROI Mining Candidates v29 报告

日期：2026-06-15

## 目的

继续从未标注非 random task20 候选中补 trajectory ROI 标签，目标是越过正 ROI 50 和训练样本 150 的最低线。

## 机器字段

```json
{
  "all_non_random": true,
  "all_task20": true,
  "available_unlabeled_non_random_candidate_count": 50,
  "candidate_count": 22,
  "candidate_family_region_counts": {
    "greedy-anchor|apollo15_20km": 6,
    "greedy-anchor|tranquillitatis_balmer_like_20km": 6,
    "sector-wave|apollo15_20km": 6,
    "sector-wave|tranquillitatis_balmer_like_20km": 4
  },
  "certificate_ready": false,
  "decision_counts": {
    "DELAY_QUEUE": 15,
    "HIGH_PRIORITY": 7
  },
  "impact_bucket_counts": {
    "": 8,
    "new_support_changing": 12,
    "new_task_set": 2
  },
  "production_ready": false,
  "schema_version": "gat_positive_roi_mining_candidates_v29",
  "selected_candidates": [
    {
      "cell_positive_rate": 0.482759,
      "decision_name": "DELAY_QUEUE",
      "impact": "new_support_changing",
      "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json",
      "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_4848230110b93844_18_3_11",
      "ordinal_positive_rate": 0.25,
      "score": 10.27335,
      "target_sequence": [
        18,
        3,
        11
      ]
    },
    {
      "cell_positive_rate": 0.482759,
      "decision_name": "DELAY_QUEUE",
      "impact": "new_support_changing",
      "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json",
      "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_94206d715106bf37_15_6_2_4_1_11",
      "ordinal_positive_rate": 0.25,
      "score": 9.996944,
      "target_sequence": [
        15,
        6,
        2,
        4,
        1,
        11
      ]
    },
    {
      "cell_positive_rate": 0.482759,
      "decision_name": "DELAY_QUEUE",
      "impact": "new_support_changing",
      "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json",
      "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_c5025a0583f6ea6c_13_12_3_5",
      "ordinal_positive_rate": 0.25,
      "score": 9.930375,
      "target_sequence": [
        13,
        12,
        3,
        5
      ]
    },
    {
      "cell_positive_rate": 0.482759,
      "decision_name": "DELAY_QUEUE",
      "impact": "new_support_changing",
      "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json",
      "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_7390856b04698300_8_16_9_20",
      "ordinal_positive_rate": 0.25,
      "score": 9.915873,
      "target_sequence": [
        8,
        16,
        9,
        20
      ]
    },
    {
      "cell_positive_rate": 0.333333,
      "decision_name": "DELAY_QUEUE",
      "impact": "new_support_changing",
      "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json",
      "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_27b61a4367a5c961_4_19_3",
      "ordinal_positive_rate": 0.0,
      "score": 9.884817,
      "target_sequence": [
        4,
        19,
        3
      ]
    },
    {
      "cell_positive_rate": 0.333333,
      "decision_name": "DELAY_QUEUE",
      "impact": "new_support_changing",
      "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_10_seed61948_logical_graph.json",
      "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_10_seed61948_a05232b2b6c99641_18_4_11_5",
      "ordinal_positive_rate": 0.0,
      "score": 9.821491,
      "target_sequence": [
        18,
        4,
        11,
        5
      ]
    },
    {
      "cell_positive_rate": 0.482759,
      "decision_name": "HIGH_PRIORITY",
      "impact": "new_task_set",
      "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json",
      "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_07e693c5f161a590_18_5_4_14_17",
      "ordinal_positive_rate": 0.4,
      "score": 9.763777,
      "target_sequence": [
        18,
        5,
        4,
        14,
        17
      ]
    },
    {
      "cell_positive_rate": 0.333333,
      "decision_name": "DELAY_QUEUE",
      "impact": "new_support_changing",
      "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json",
      "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_8_14_11_9_17_5",
      "ordinal_positive_rate": 0.0,
      "score": 9.750377,
      "target_sequence": [
        8,
        14,
        11,
        9,
        17,
        5
      ]
    },
    {
      "cell_positive_rate": 0.333333,
      "decision_name": "DELAY_QUEUE",
      "impact": "new_support_changing",
      "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json",
      "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_d067a87292522613_8_12_18_5",
      "ordinal_positive_rate": 0.0,
      "score": 9.719287,
      "target_sequence": [
        8,
        12,
        18,
        5
      ]
    },
    {
      "cell_positive_rate": 0.333333,
      "decision_name": "DELAY_QUEUE",
      "impact": "new_support_changing",
      "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json",
      "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_d067a87292522613_4_3_19_18_5",
      "ordinal_positive_rate": 0.0,
      "score": 9.702368,
      "target_sequence": [
        4,
        3,
        19,
        18,
        5
      ]
    },
    {
      "cell_positive_rate": 0.482759,
      "decision_name": "HIGH_PRIORITY",
      "impact": "new_task_set",
      "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json",
      "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_37e3048dada58785_2_6_12_13_7_17",
      "ordinal_positive_rate": 0.4,
      "score": 9.684858,
      "target_sequence": [
        2,
        6,
        12,
        13,
        7,
        17
      ]
    },
    {
      "cell_positive_rate": 0.333333,
      "decision_name": "DELAY_QUEUE",
      "impact": "new_support_changing",
      "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json",
      "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_7714263901aeb2ec_8_14_19",
      "ordinal_positive_rate": 0.0,
      "score": 9.607709,
      "target_sequence": [
        8,
        14,
        19
      ]
    },
    {
      "cell_positive_rate": 0.37931,
      "decision_name": "HIGH_PRIORITY",
      "impact": "new_support_changing",
      "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json",
      "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_39ec05e43b291642_5_8_18_16_9",
      "ordinal_positive_rate": 0.25,
      "score": 9.40328,
      "target_sequence": [
        5,
        8,
        18,
        16,
        9
      ]
    },
    {
      "cell_positive_rate": 0.37931,
      "decision_name": "HIGH_PRIORITY",
      "impact": null,
      "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
      "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_3d1bd8618099b573_8_17_15",
      "ordinal_positive_rate": 0.4,
      "score": 9.005911,
      "target_sequence": [
        8,
        17,
        15
      ]
    },
    {
      "cell_positive_rate": 0.266667,
      "decision_name": "DELAY_QUEUE",
      "impact": "new_support_changing",
      "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612_logical_graph.json",
      "name": "apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_ce3508e12ad69da7_16_5_10_14",
      "ordinal_positive_rate": 0.0,
      "score": 8.583637,
      "target_sequence": [
        16,
        5,
        10,
        14
      ]
    },
    {
      "cell_positive_rate": 0.266667,
      "decision_name": "DELAY_QUEUE",
      "impact": null,
      "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
      "name": "apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_68f9b4e3d7515691_7_6_1_19_2_8",
      "ordinal_positive_rate": 0.5,
      "score": 8.513141,
      "target_sequence": [
        7,
        6,
        1,
        19,
        2,
        8
      ]
    },
    {
      "cell_positive_rate": 0.266667,
      "decision_name": "DELAY_QUEUE",
      "impact": null,
      "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
      "name": "apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_f29ac739f3cb5226_3_5_4_2_10",
      "ordinal_positive_rate": 0.5,
      "score": 8.472458,
      "target_sequence": [
        3,
        5,
        4,
        2,
        10
      ]
    },
    {
      "cell_positive_rate": 0.266667,
      "decision_name": "DELAY_QUEUE",
      "impact": null,
      "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
      "name": "apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_ee378d5c9364745a_7_14_6_19_11",
      "ordinal_positive_rate": 0.5,
      "score": 8.3704,
      "target_sequence": [
        7,
        14,
        6,
        19,
        11
      ]
    },
    {
      "cell_positive_rate": 0.37931,
      "decision_name": "HIGH_PRIORITY",
      "impact": null,
      "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
      "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_16_17_15",
      "ordinal_positive_rate": 0.4,
      "score": 8.339646,
      "target_sequence": [
        16,
        17,
        15
      ]
    },
    {
      "cell_positive_rate": 0.266667,
      "decision_name": "DELAY_QUEUE",
      "impact": null,
      "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
      "name": "apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_04c4d16cf38f75d9_9_5_11_4_2_8",
      "ordinal_positive_rate": 0.5,
      "score": 8.249505,
      "target_sequence": [
        9,
        5,
        11,
        4,
        2,
        8
      ]
    },
    {
      "cell_positive_rate": 0.37931,
      "decision_name": "HIGH_PRIORITY",
      "impact": null,
      "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
      "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_17ccb5dc2e9bbac0_5_10_15",
      "ordinal_positive_rate": 0.4,
      "score": 7.663916,
      "target_sequence": [
        5,
        10,
        15
      ]
    },
    {
      "cell_positive_rate": 0.266667,
      "decision_name": "HIGH_PRIORITY",
      "impact": null,
      "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json",
      "name": "apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_1_18",
      "ordinal_positive_rate": 0.0,
      "score": 7.629654,
      "target_sequence": [
        1,
        18
      ]
    }
  ],
  "source_candidate_file_count": 49,
  "training_label_requires_worker_ab": true
}
```

## 结论

- 这些候选不是训练标签，必须经过 worker A/B audit 后才能进入 GAT ROI 训练集。
- 采样策略只影响候选顺序；不参与证书，不默认启用 production。
