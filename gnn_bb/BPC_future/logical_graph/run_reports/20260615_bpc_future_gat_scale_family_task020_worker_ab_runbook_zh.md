# GAT Target-Priority Worker A/B Runbook

日期：2026-06-14

## 目的

生成下一轮 5/10 no-regression 与 20-task ROI A/B 命令。GAT 仍只负责 embedding / trajectory impact 表达，kNN/OOD 只做安全壳；通过安全壳的 true-RC negative 可优先进入 worker target，不通过的负列进入 DELAY_QUEUE，不能永久丢弃，也不能参与 certificate。

## 机器字段

```text
gat_target_priority_worker_ab_runbook = current
status = ready
production_ready = false
default_enabled = false
certificate_ready = false
official_bound_effect = false
required_candidate_context_field_count = 8
all_checks_pass = true
```

## Candidate Policy

```json
{
  "certificate_effect": false,
  "context_miss_policy": "capture_actual_reached_contexts_for_next_iteration",
  "gat_role": "embedding_and_trajectory_impact_expression",
  "knn_ood_role": "safety_shell",
  "negative_discard_allowed": false,
  "safe_negative_action": "HIGH_PRIORITY",
  "unsafe_negative_action": "DELAY_QUEUE",
  "worker_stage_policy": "match_capture_pricing_kind: heuristic_before_heuristic_exact_before_exact"
}
```

## Candidate Runs

```json
[
  {
    "active_hash_before": "db1b163885849bab",
    "baseline_csv": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_5_1_2_18_3_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "d519291840dd7000",
    "forbidden_signature_hash": "8c559ff7a164a116",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_5_1_2_18_3",
    "pool_signature_hash": "530406beed850f36",
    "pool_task_set_hash": "e8b7e3dc10f8202e",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->5:low_risk:2",
      "5->1:low_risk:2",
      "1->2:low_risk:2",
      "2->18:low_time:0",
      "18->3:low_risk:2",
      "3->0:low_time:0"
    ],
    "target_priority_sequence": [
      5,
      1,
      2,
      18,
      3
    ],
    "target_sequence": [
      5,
      1,
      2,
      18,
      3
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->5:low_risk:2",
          "5->1:low_risk:2",
          "1->2:low_risk:2",
          "2->18:low_time:0",
          "18->3:low_risk:2",
          "3->0:low_time:0"
        ],
        "sequence": [
          5,
          1,
          2,
          18,
          3
        ],
        "start_time": 11.291563
      }
    ],
    "true_dual_hash": "7a8482acd5dc4633",
    "worker_csv": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_5_1_2_18_3_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "8fea27ca936f24d2",
    "baseline_csv": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_5_1_15_3_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "67c11b5ec80925ec",
    "forbidden_signature_hash": "19812e842cb95df9",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_5_1_15_3",
    "pool_signature_hash": "549b0ebff4d503f5",
    "pool_task_set_hash": "27845f832af78f68",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->5:low_risk:2",
      "5->1:low_risk:2",
      "1->15:low_time:0",
      "15->3:low_time:0",
      "3->0:low_risk:2"
    ],
    "target_priority_sequence": [
      5,
      1,
      15,
      3
    ],
    "target_sequence": [
      5,
      1,
      15,
      3
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->5:low_risk:2",
          "5->1:low_risk:2",
          "1->15:low_time:0",
          "15->3:low_time:0",
          "3->0:low_risk:2"
        ],
        "sequence": [
          5,
          1,
          15,
          3
        ],
        "start_time": 11.291563
      }
    ],
    "true_dual_hash": "8d0b48016c368950",
    "worker_csv": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_5_1_15_3_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "3341a4ba541bfa32",
    "baseline_csv": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_2_1_5_3_12_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "62c86745ed2b3aaa",
    "forbidden_signature_hash": "ddf56f63968049f0",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_2_1_5_3_12",
    "pool_signature_hash": "50dc555c1757eeca",
    "pool_task_set_hash": "fdf2e77ba9b76816",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->2:low_risk:1",
      "2->1:low_time:0",
      "1->5:low_risk:2",
      "5->0:low_time:0"
    ],
    "target_priority_sequence": [
      2,
      1,
      5
    ],
    "target_sequence": [
      2,
      1,
      5,
      3,
      12
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->2:low_risk:1",
          "2->1:low_time:0",
          "1->5:low_risk:2",
          "5->0:low_time:0"
        ],
        "sequence": [
          2,
          1,
          5
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->3:low_risk:2",
          "3->12:low_risk:1",
          "12->0:low_risk:2"
        ],
        "sequence": [
          3,
          12
        ],
        "start_time": 228.218699
      }
    ],
    "true_dual_hash": "9bd9a1d18b7a5cf5",
    "worker_csv": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_2_1_5_3_12_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "a8681375b98abe9b",
    "baseline_csv": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_8_4_5_16_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "ddcb5387bef3bf63",
    "forbidden_signature_hash": "30f21d8900d08486",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_8_4_5_16",
    "pool_signature_hash": "9434aed561bacc3e",
    "pool_task_set_hash": "e4123a7322872a6a",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->8:low_energy:1",
      "8->4:low_time:0",
      "4->5:low_time:0",
      "5->16:low_time:0",
      "16->0:low_time:0"
    ],
    "target_priority_sequence": [
      8,
      4,
      5,
      16
    ],
    "target_sequence": [
      8,
      4,
      5,
      16
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->8:low_energy:1",
          "8->4:low_time:0",
          "4->5:low_time:0",
          "5->16:low_time:0",
          "16->0:low_time:0"
        ],
        "sequence": [
          8,
          4,
          5,
          16
        ],
        "start_time": 81.406191
      }
    ],
    "true_dual_hash": "755b99c23a4b6c8e",
    "worker_csv": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_8_4_5_16_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "a4c0969f3e85a752",
    "baseline_csv": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_5c522ff2995f86be_11_1_13_20_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "5c522ff2995f86be",
    "forbidden_signature_hash": "626c424ddedf4f80",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_5c522ff2995f86be_11_1_13_20",
    "pool_signature_hash": "51167fe6d51c9788",
    "pool_task_set_hash": "a07b207bdd9a5b98",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->11:low_energy:1",
      "11->0:low_time:0"
    ],
    "target_priority_sequence": [
      11
    ],
    "target_sequence": [
      11,
      1,
      13,
      20
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->11:low_energy:1",
          "11->0:low_time:0"
        ],
        "sequence": [
          11
        ],
        "start_time": 79.265081
      },
      {
        "arc_option_sequence": [
          "0->1:low_risk:2",
          "1->13:low_risk:2",
          "13->20:low_risk:2",
          "20->0:low_risk:2"
        ],
        "sequence": [
          1,
          13,
          20
        ],
        "start_time": 188.985007
      }
    ],
    "true_dual_hash": "88344526d1d391bd",
    "worker_csv": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_5c522ff2995f86be_11_1_13_20_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "51df5d79e9ac45ae",
    "baseline_csv": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_08b8d772e2ab9623_8_16_11_15_18_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "08b8d772e2ab9623",
    "forbidden_signature_hash": "0c230e1a6c7fee96",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_08b8d772e2ab9623_8_16_11_15_18",
    "pool_signature_hash": "07ce45c4b7ea1c45",
    "pool_task_set_hash": "ba7679f84bbb38ae",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->8:low_risk:2",
      "8->16:low_risk:2",
      "16->11:low_risk:2",
      "11->0:low_risk:2"
    ],
    "target_priority_sequence": [
      8,
      16,
      11
    ],
    "target_sequence": [
      8,
      16,
      11,
      15,
      18
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->8:low_risk:2",
          "8->16:low_risk:2",
          "16->11:low_risk:2",
          "11->0:low_risk:2"
        ],
        "sequence": [
          8,
          16,
          11
        ],
        "start_time": 14.542572
      },
      {
        "arc_option_sequence": [
          "0->15:low_time:0",
          "15->18:low_risk:2",
          "18->0:low_time:0"
        ],
        "sequence": [
          15,
          18
        ],
        "start_time": 302.871307
      }
    ],
    "true_dual_hash": "c923eda9f0bcc8d2",
    "worker_csv": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_08b8d772e2ab9623_8_16_11_15_18_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "622200ad1fc583cc",
    "baseline_csv": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_e897b76f2888f822_17_11_14_9_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "e897b76f2888f822",
    "forbidden_signature_hash": "7b7bc18b58faa1db",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_e897b76f2888f822_17_11_14_9",
    "pool_signature_hash": "cbd4c17130829b87",
    "pool_task_set_hash": "71fc2cca8fb5ace4",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->17:low_time:0",
      "17->11:low_risk:2",
      "11->0:low_risk:2"
    ],
    "target_priority_sequence": [
      17,
      11
    ],
    "target_sequence": [
      17,
      11,
      14,
      9
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->17:low_time:0",
          "17->11:low_risk:2",
          "11->0:low_risk:2"
        ],
        "sequence": [
          17,
          11
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->14:low_time:0",
          "14->9:low_risk:2",
          "9->0:low_risk:2"
        ],
        "sequence": [
          14,
          9
        ],
        "start_time": 292.997503
      }
    ],
    "true_dual_hash": "ed98088cdfa83a03",
    "worker_csv": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_e897b76f2888f822_17_11_14_9_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "e00e5f54b69345ba",
    "baseline_csv": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_9eb0dc7839bf91ec_2_17_16_13_18_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "9eb0dc7839bf91ec",
    "forbidden_signature_hash": "eefa5f433de1f487",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_9eb0dc7839bf91ec_2_17_16_13_18",
    "pool_signature_hash": "8c1c94d7b1c2c4b2",
    "pool_task_set_hash": "3b02449ad82d2dc3",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->2:low_time:0",
      "2->17:low_risk:1",
      "17->16:low_time:0",
      "16->0:low_time:0"
    ],
    "target_priority_sequence": [
      2,
      17,
      16
    ],
    "target_sequence": [
      2,
      17,
      16,
      13,
      18
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->2:low_time:0",
          "2->17:low_risk:1",
          "17->16:low_time:0",
          "16->0:low_time:0"
        ],
        "sequence": [
          2,
          17,
          16
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->13:low_risk:2",
          "13->18:low_time:0",
          "18->0:low_time:0"
        ],
        "sequence": [
          13,
          18
        ],
        "start_time": 336.687825
      }
    ],
    "true_dual_hash": "4fa661248332899c",
    "worker_csv": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_9eb0dc7839bf91ec_2_17_16_13_18_target_priority_worker/results.csv"
  }
]
```

## Commands

### task005_mainline_no_regression_gat_kept

Run task-5 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_5_journey.yaml --time-limit 30.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task005_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task005_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task005_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task005_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_005/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks005_01_seed2046000_logical_graph.json BPC_future/logical_graph/tasks_005/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_01_seed2146011_logical_graph.json
```

### task010_mainline_no_regression_gat_kept

Run task-10 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_10_journey.yaml --time-limit 30.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task010_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task010_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task010_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task010_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_010/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json BPC_future/logical_graph/tasks_010/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_5_1_2_18_3_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_5_1_2_18_3_mainline_baseline/results.csv --log-dir BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_5_1_2_18_3_mainline_baseline/logs --solution-dir BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_5_1_2_18_3_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_5_1_2_18_3_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_5_1_2_18_3_target_priority_worker/results.csv --log-dir BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_5_1_2_18_3_target_priority_worker/logs --solution-dir BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_5_1_2_18_3_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=d519291840dd7000 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=5,1,2,18,3 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=5,1,2,18,3 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=5,1,2,18,3 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->5:low_risk:2","5->1:low_risk:2","1->2:low_risk:2","2->18:low_time:0","18->3:low_risk:2","3->0:low_time:0"],"sequence":[5,1,2,18,3],"start_time":11.291563}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->5:low_risk:2,5->1:low_risk:2,1->2:low_risk:2,2->18:low_time:0,18->3:low_risk:2,3->0:low_time:0'
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_5_1_15_3_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_5_1_15_3_mainline_baseline/results.csv --log-dir BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_5_1_15_3_mainline_baseline/logs --solution-dir BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_5_1_15_3_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_5_1_15_3_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_5_1_15_3_target_priority_worker/results.csv --log-dir BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_5_1_15_3_target_priority_worker/logs --solution-dir BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_5_1_15_3_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=67c11b5ec80925ec --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=5,1,15,3 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=5,1,15,3 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=5,1,15,3 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->5:low_risk:2","5->1:low_risk:2","1->15:low_time:0","15->3:low_time:0","3->0:low_risk:2"],"sequence":[5,1,15,3],"start_time":11.291563}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->5:low_risk:2,5->1:low_risk:2,1->15:low_time:0,15->3:low_time:0,3->0:low_risk:2'
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_2_1_5_3_12_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_2_1_5_3_12_mainline_baseline/results.csv --log-dir BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_2_1_5_3_12_mainline_baseline/logs --solution-dir BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_2_1_5_3_12_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_2_1_5_3_12_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_2_1_5_3_12_target_priority_worker/results.csv --log-dir BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_2_1_5_3_12_target_priority_worker/logs --solution-dir BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_2_1_5_3_12_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=62c86745ed2b3aaa --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=2,1,5 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=2,1,5 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=2,1,5,3,12 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->2:low_risk:1","2->1:low_time:0","1->5:low_risk:2","5->0:low_time:0"],"sequence":[2,1,5],"start_time":0.0},{"arc_option_sequence":["0->3:low_risk:2","3->12:low_risk:1","12->0:low_risk:2"],"sequence":[3,12],"start_time":228.218699}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->2:low_risk:1,2->1:low_time:0,1->5:low_risk:2,5->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_8_4_5_16_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_8_4_5_16_mainline_baseline/results.csv --log-dir BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_8_4_5_16_mainline_baseline/logs --solution-dir BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_8_4_5_16_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_8_4_5_16_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_8_4_5_16_target_priority_worker/results.csv --log-dir BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_8_4_5_16_target_priority_worker/logs --solution-dir BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_8_4_5_16_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=ddcb5387bef3bf63 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=8,4,5,16 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=8,4,5,16 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=8,4,5,16 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->8:low_energy:1","8->4:low_time:0","4->5:low_time:0","5->16:low_time:0","16->0:low_time:0"],"sequence":[8,4,5,16],"start_time":81.406191}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->8:low_energy:1,8->4:low_time:0,4->5:low_time:0,5->16:low_time:0,16->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_5c522ff2995f86be_11_1_13_20_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_5c522ff2995f86be_11_1_13_20_mainline_baseline/results.csv --log-dir BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_5c522ff2995f86be_11_1_13_20_mainline_baseline/logs --solution-dir BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_5c522ff2995f86be_11_1_13_20_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_5c522ff2995f86be_11_1_13_20_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_5c522ff2995f86be_11_1_13_20_target_priority_worker/results.csv --log-dir BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_5c522ff2995f86be_11_1_13_20_target_priority_worker/logs --solution-dir BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_5c522ff2995f86be_11_1_13_20_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=5c522ff2995f86be --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=11 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=11 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=11,1,13,20 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->11:low_energy:1","11->0:low_time:0"],"sequence":[11],"start_time":79.265081},{"arc_option_sequence":["0->1:low_risk:2","1->13:low_risk:2","13->20:low_risk:2","20->0:low_risk:2"],"sequence":[1,13,20],"start_time":188.985007}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->11:low_energy:1,11->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_08b8d772e2ab9623_8_16_11_15_18_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_08b8d772e2ab9623_8_16_11_15_18_mainline_baseline/results.csv --log-dir BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_08b8d772e2ab9623_8_16_11_15_18_mainline_baseline/logs --solution-dir BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_08b8d772e2ab9623_8_16_11_15_18_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_08b8d772e2ab9623_8_16_11_15_18_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_08b8d772e2ab9623_8_16_11_15_18_target_priority_worker/results.csv --log-dir BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_08b8d772e2ab9623_8_16_11_15_18_target_priority_worker/logs --solution-dir BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_08b8d772e2ab9623_8_16_11_15_18_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=08b8d772e2ab9623 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=8,16,11 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=8,16,11 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=8,16,11,15,18 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->8:low_risk:2","8->16:low_risk:2","16->11:low_risk:2","11->0:low_risk:2"],"sequence":[8,16,11],"start_time":14.542572},{"arc_option_sequence":["0->15:low_time:0","15->18:low_risk:2","18->0:low_time:0"],"sequence":[15,18],"start_time":302.871307}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->8:low_risk:2,8->16:low_risk:2,16->11:low_risk:2,11->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_e897b76f2888f822_17_11_14_9_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_e897b76f2888f822_17_11_14_9_mainline_baseline/results.csv --log-dir BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_e897b76f2888f822_17_11_14_9_mainline_baseline/logs --solution-dir BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_e897b76f2888f822_17_11_14_9_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_e897b76f2888f822_17_11_14_9_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_e897b76f2888f822_17_11_14_9_target_priority_worker/results.csv --log-dir BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_e897b76f2888f822_17_11_14_9_target_priority_worker/logs --solution-dir BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_e897b76f2888f822_17_11_14_9_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=e897b76f2888f822 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=17,11 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=17,11 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=17,11,14,9 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->17:low_time:0","17->11:low_risk:2","11->0:low_risk:2"],"sequence":[17,11],"start_time":0.0},{"arc_option_sequence":["0->14:low_time:0","14->9:low_risk:2","9->0:low_risk:2"],"sequence":[14,9],"start_time":292.997503}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->17:low_time:0,17->11:low_risk:2,11->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_9eb0dc7839bf91ec_2_17_16_13_18_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_9eb0dc7839bf91ec_2_17_16_13_18_mainline_baseline/results.csv --log-dir BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_9eb0dc7839bf91ec_2_17_16_13_18_mainline_baseline/logs --solution-dir BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_9eb0dc7839bf91ec_2_17_16_13_18_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_9eb0dc7839bf91ec_2_17_16_13_18_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_9eb0dc7839bf91ec_2_17_16_13_18_target_priority_worker/results.csv --log-dir BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_9eb0dc7839bf91ec_2_17_16_13_18_target_priority_worker/logs --solution-dir BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_9eb0dc7839bf91ec_2_17_16_13_18_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=9eb0dc7839bf91ec --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=2,17,16 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=2,17,16 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=2,17,16,13,18 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->2:low_time:0","2->17:low_risk:1","17->16:low_time:0","16->0:low_time:0"],"sequence":[2,17,16],"start_time":0.0},{"arc_option_sequence":["0->13:low_risk:2","13->18:low_time:0","18->0:low_time:0"],"sequence":[13,18],"start_time":336.687825}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->2:low_time:0,2->17:low_risk:1,17->16:low_time:0,16->0:low_time:0'
```

## 边界

- 5/10 命令不关闭主线 GAT/learning，也不启用新 worker；
- 20 baseline/worker 命令也不关闭主线 GAT/learning，避免候选捕获上下文无法复现；
- 20 baseline/worker 命令开启 counterfactual replay capture；如果旧 target context 没到，仍保留实际到达的 context 供下一轮候选抽取；
- 20 worker 命令是显式 opt-in，只验证 target-priority ROI；
- 20 worker 候选必须带完整 context / dual / cuts / branch / pool hash；
- 所有命令都不启用 sharded Pulse certificate 或 official lower-bound effect；
- 含 `->` 的 arc-option 配置通过 `shlex.join` 自动引用，不能手工去掉引号；
- 该 runbook 不是生产开关，跑完后仍需看 5/10 no-regression 和 20-task ROI。
