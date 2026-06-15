# GAT Positive ROI Mining Candidates v30 报告

日期：2026-06-15

## 目的

在 v29 合并后仍差 2 个正 trajectory ROI 的情况下，从未标注、非 random、task20 候选中选取一小批高历史 ROI 单元候选，继续做 paired worker A/B 标签采集。

## 机器字段

```json
{
  "all_non_random": true,
  "all_task20": true,
  "available_unlabeled_non_random_candidate_count": 22,
  "candidate_count": 8,
  "candidate_family_region_counts": {
    "greedy-anchor|apollo15_20km": 6,
    "greedy-anchor|tranquillitatis_balmer_like_20km": 2
  },
  "certificate_ready": false,
  "decision_counts": {
    "DELAY_QUEUE": 4,
    "HIGH_PRIORITY": 4
  },
  "impact_bucket_counts": {
    "new_support_changing": 4,
    "new_task_set": 4
  },
  "production_ready": false,
  "schema_version": "gat_positive_roi_mining_candidates_v30",
  "selected_candidates": [
    {
      "cell_positive_rate": 0.457143,
      "decision_name": "DELAY_QUEUE",
      "impact": "new_support_changing",
      "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json",
      "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_33c54245da27321e_16_17_19",
      "ordinal_positive_rate": 0.457143,
      "score": 12.358695,
      "target_sequence": [
        16,
        17,
        19
      ]
    },
    {
      "cell_positive_rate": 0.457143,
      "decision_name": "DELAY_QUEUE",
      "impact": "new_support_changing",
      "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json",
      "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_7390856b04698300_12_8_16_9_20",
      "ordinal_positive_rate": 0.457143,
      "score": 12.356544,
      "target_sequence": [
        12,
        8,
        16,
        9,
        20
      ]
    },
    {
      "cell_positive_rate": 0.457143,
      "decision_name": "DELAY_QUEUE",
      "impact": "new_task_set",
      "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json",
      "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_33788d6b7bdf8387_13_12_8_16_9_20",
      "ordinal_positive_rate": 0.457143,
      "score": 11.859159,
      "target_sequence": [
        13,
        12,
        8,
        16,
        9,
        20
      ]
    },
    {
      "cell_positive_rate": 0.457143,
      "decision_name": "HIGH_PRIORITY",
      "impact": "new_task_set",
      "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json",
      "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b1fb77954b949bf0_6_12_13_7_17_14",
      "ordinal_positive_rate": 0.457143,
      "score": 11.711389,
      "target_sequence": [
        6,
        12,
        13,
        7,
        17,
        14
      ]
    },
    {
      "cell_positive_rate": 0.457143,
      "decision_name": "HIGH_PRIORITY",
      "impact": "new_support_changing",
      "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json",
      "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_84ae11479ed592d4_13_17_11_5",
      "ordinal_positive_rate": 0.457143,
      "score": 11.071451,
      "target_sequence": [
        13,
        17,
        11,
        5
      ]
    },
    {
      "cell_positive_rate": 0.457143,
      "decision_name": "HIGH_PRIORITY",
      "impact": "new_support_changing",
      "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json",
      "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_4c81d9ecf77097c9_8_4_10",
      "ordinal_positive_rate": 0.457143,
      "score": 10.989054,
      "target_sequence": [
        8,
        4,
        10
      ]
    },
    {
      "cell_positive_rate": 0.3125,
      "decision_name": "DELAY_QUEUE",
      "impact": "new_task_set",
      "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json",
      "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_7_12",
      "ordinal_positive_rate": 0.3125,
      "score": 9.00748,
      "target_sequence": [
        7,
        12
      ]
    },
    {
      "cell_positive_rate": 0.3125,
      "decision_name": "HIGH_PRIORITY",
      "impact": "new_task_set",
      "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json",
      "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_11_15_6",
      "ordinal_positive_rate": 0.3125,
      "score": 8.593988,
      "target_sequence": [
        11,
        15,
        6
      ]
    }
  ],
  "source_candidate_file_count": 50,
  "training_label_requires_worker_ab": true
}
```
