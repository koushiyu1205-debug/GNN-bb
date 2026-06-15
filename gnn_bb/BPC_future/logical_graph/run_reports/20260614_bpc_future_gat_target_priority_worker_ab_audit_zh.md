# GAT Target-Priority Worker A/B Audit 报告

日期：2026-06-14

## 目的

聚合 GAT target-priority worker A/B 的 CSV 结果，判断候选是否有真实 ROI。
该脚本只读 CSV，不运行 BPC / pricing / RMP，不启用 worker，不产生 certificate。

## 机器字段

```text
gat_target_priority_worker_ab_audit = current
status = audited
record_count = 13
roi_class_counts = {'no_observed_roi': 11, 'positive_primal_roi': 2}
production_ready = false
default_enabled = false
certificate_ready = false
official_bound_effect = false
all_checks_pass = true
```

## Records

```json
[
  {
    "baseline_columns": 257,
    "baseline_csv": "BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo20_sector_wave_c488c428_target_20_17_16_no_learning_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 6,
    "baseline_fallback_used": false,
    "baseline_primal": 740.122399,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 2,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "c488c428ee5822de",
    "generated_sequences_delta": 1733,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json",
    "name": "apollo20_sector_wave_c488c428_target_20_17_16",
    "official_bound_effect": false,
    "primal_improvement": 0.9636629999999968,
    "roi_class": "positive_primal_roi",
    "target_arc_option_sequence": [
      "0->20:low_risk:2",
      "20->17:low_risk:2",
      "17->16:low_risk:2",
      "16->0:low_risk:2"
    ],
    "target_sequence": [
      20,
      17,
      16
    ],
    "worker_columns": 259,
    "worker_csv": "BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo20_sector_wave_c488c428_target_20_17_16_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_primal": 739.158736,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 257,
    "baseline_csv": "BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo20_sector_wave_c488c428_target_20_17_16_no_learning_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 6,
    "baseline_fallback_used": true,
    "baseline_primal": 740.122399,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 0,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "7e0afd09753effed",
    "generated_sequences_delta": 121,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_7e0afd09753effed_19",
    "official_bound_effect": false,
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi",
    "target_arc_option_sequence": [
      "0->19:low_risk:2",
      "19->0:low_risk:2"
    ],
    "target_sequence": [
      19
    ],
    "worker_columns": 257,
    "worker_csv": "BPC_future/results/gat_target_priority_worker_ab_auto_candidates_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_7e0afd09753effed_19_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 6,
    "worker_primal": 740.122399,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 257,
    "baseline_csv": "BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo20_sector_wave_c488c428_target_20_17_16_no_learning_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 6,
    "baseline_fallback_used": true,
    "baseline_primal": 740.122399,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 0,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "a3b5b5263e1cfe17",
    "generated_sequences_delta": 9,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_a3b5b5263e1cfe17_14_5_8_18_12",
    "official_bound_effect": false,
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi",
    "target_arc_option_sequence": [
      "0->14:low_time:0",
      "14->5:low_risk:2",
      "5->8:low_time:0",
      "8->18:low_risk:2",
      "18->12:low_risk:2",
      "12->0:low_risk:2"
    ],
    "target_sequence": [
      14,
      5,
      8,
      18,
      12
    ],
    "worker_columns": 257,
    "worker_csv": "BPC_future/results/gat_target_priority_worker_ab_auto_candidates_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_a3b5b5263e1cfe17_14_5_8_18_12_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 6,
    "worker_primal": 740.122399,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 395,
    "baseline_csv": "BPC_future/results/gat_target_priority_worker_ab_auto_candidates_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_05_seed61408_de2c1d84615d5c71_14_6_1_20_9_no_learning_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 9,
    "baseline_fallback_used": false,
    "baseline_primal": 752.490126,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 0,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "de2c1d84615d5c71",
    "generated_sequences_delta": -115,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_05_seed61408_de2c1d84615d5c71_14_6_1_20_9",
    "official_bound_effect": false,
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi",
    "target_arc_option_sequence": [
      "0->14:low_risk:2",
      "14->6:low_risk:2",
      "6->1:low_risk:2",
      "1->20:low_time:0",
      "20->9:low_risk:2",
      "9->0:low_risk:2"
    ],
    "target_sequence": [
      14,
      6,
      1,
      20,
      9
    ],
    "worker_columns": 395,
    "worker_csv": "BPC_future/results/gat_target_priority_worker_ab_auto_candidates_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_05_seed61408_de2c1d84615d5c71_14_6_1_20_9_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 9,
    "worker_primal": 752.490126,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 395,
    "baseline_csv": "BPC_future/results/gat_target_priority_worker_ab_auto_candidates_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_05_seed61408_de2c1d84615d5c71_14_6_1_20_9_no_learning_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 9,
    "baseline_fallback_used": true,
    "baseline_primal": 752.490126,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 0,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "157f03afc868de3b",
    "generated_sequences_delta": 75,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_05_seed61408_157f03afc868de3b_13",
    "official_bound_effect": false,
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi",
    "target_arc_option_sequence": [
      "0->13:low_risk:2",
      "13->0:low_risk:2"
    ],
    "target_sequence": [
      13
    ],
    "worker_columns": 395,
    "worker_csv": "BPC_future/results/gat_target_priority_worker_ab_auto_candidates_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_05_seed61408_157f03afc868de3b_13_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 9,
    "worker_primal": 752.490126,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 257,
    "baseline_csv": "BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo20_sector_wave_c488c428_target_20_17_16_no_learning_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 6,
    "baseline_fallback_used": true,
    "baseline_primal": 740.122399,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 2,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "c488c428ee5822de",
    "generated_sequences_delta": 1700,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_c488c428ee5822de_20_17_16",
    "official_bound_effect": false,
    "primal_improvement": 0.9636629999999968,
    "roi_class": "positive_primal_roi",
    "target_arc_option_sequence": [
      "0->20:low_risk:2",
      "20->17:low_risk:2",
      "17->16:low_risk:2",
      "16->0:low_risk:2"
    ],
    "target_sequence": [
      20,
      17,
      16
    ],
    "worker_columns": 259,
    "worker_csv": "BPC_future/results/gat_target_priority_worker_ab_20roi_smoke_auto_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_c488c428ee5822de_20_17_16_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_primal": 739.158736,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 395,
    "baseline_csv": "BPC_future/results/gat_target_priority_worker_ab_family_20260614/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_3d1bd8618099b573_8_no_learning_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 3,
    "baseline_fallback_used": false,
    "baseline_primal": 651.444167,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 0,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "3d1bd8618099b573",
    "generated_sequences_delta": 84,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_3d1bd8618099b573_8",
    "official_bound_effect": false,
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi",
    "target_arc_option_sequence": [
      "0->8:low_risk:2",
      "8->0:low_risk:2"
    ],
    "target_sequence": [
      8
    ],
    "worker_columns": 395,
    "worker_csv": "BPC_future/results/gat_target_priority_worker_ab_family_20260614/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_3d1bd8618099b573_8_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 3,
    "worker_primal": 651.444167,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 461,
    "baseline_csv": "BPC_future/results/gat_target_priority_worker_ab_family_20260614/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_d44af494d156d43e_6_no_learning_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 3,
    "baseline_fallback_used": false,
    "baseline_primal": 556.566894,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 0,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "d44af494d156d43e",
    "generated_sequences_delta": -386,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_d44af494d156d43e_6",
    "official_bound_effect": false,
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi",
    "target_arc_option_sequence": [
      "0->6:low_risk:2",
      "6->0:low_time:0"
    ],
    "target_sequence": [
      6
    ],
    "worker_columns": 461,
    "worker_csv": "BPC_future/results/gat_target_priority_worker_ab_family_20260614/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_d44af494d156d43e_6_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 3,
    "worker_primal": 556.566894,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 290,
    "baseline_csv": "BPC_future/results/gat_target_priority_worker_ab_family_20260614/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_20_no_learning_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 3,
    "baseline_fallback_used": false,
    "baseline_primal": 647.203509,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 0,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "09187873900ecefa",
    "generated_sequences_delta": 132,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_20",
    "official_bound_effect": false,
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi",
    "target_arc_option_sequence": [
      "0->6:low_time:0",
      "6->20:low_time:0",
      "20->0:low_time:0"
    ],
    "target_sequence": [
      6,
      20
    ],
    "worker_columns": 290,
    "worker_csv": "BPC_future/results/gat_target_priority_worker_ab_family_20260614/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_20_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 3,
    "worker_primal": 647.203509,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 290,
    "baseline_csv": "BPC_future/results/gat_target_priority_worker_ab_family_20260614/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_39ec05e43b291642_20_1_no_learning_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 3,
    "baseline_fallback_used": false,
    "baseline_primal": 647.203509,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 0,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "39ec05e43b291642",
    "generated_sequences_delta": -299,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_39ec05e43b291642_20_1",
    "official_bound_effect": false,
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi",
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->1:low_time:0",
      "1->0:low_time:0"
    ],
    "target_sequence": [
      20,
      1
    ],
    "worker_columns": 290,
    "worker_csv": "BPC_future/results/gat_target_priority_worker_ab_family_20260614/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_39ec05e43b291642_20_1_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 3,
    "worker_primal": 647.203509,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 400,
    "baseline_csv": "BPC_future/results/gat_target_priority_worker_ab_family_20260614/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_07_seed61615_727eba0fe29647bc_2_no_learning_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 4,
    "baseline_fallback_used": false,
    "baseline_primal": 633.106727,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 0,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "727eba0fe29647bc",
    "generated_sequences_delta": 0,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_07_seed61615_727eba0fe29647bc_2",
    "official_bound_effect": false,
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi",
    "target_arc_option_sequence": [
      "0->2:low_risk:2",
      "2->0:low_risk:2"
    ],
    "target_sequence": [
      2
    ],
    "worker_columns": 400,
    "worker_csv": "BPC_future/results/gat_target_priority_worker_ab_family_20260614/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_07_seed61615_727eba0fe29647bc_2_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 4,
    "worker_primal": 633.106727,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 207,
    "baseline_csv": "BPC_future/results/gat_target_priority_worker_ab_family_20260614/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_e6a026e516dfd2f4_12_4_no_learning_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 3,
    "baseline_fallback_used": false,
    "baseline_primal": 664.008983,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 0,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "e6a026e516dfd2f4",
    "generated_sequences_delta": -6,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_e6a026e516dfd2f4_12_4",
    "official_bound_effect": false,
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi",
    "target_arc_option_sequence": [
      "0->12:low_risk:2",
      "12->4:low_time:0",
      "4->0:low_time:0"
    ],
    "target_sequence": [
      12,
      4
    ],
    "worker_columns": 207,
    "worker_csv": "BPC_future/results/gat_target_priority_worker_ab_family_20260614/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_e6a026e516dfd2f4_12_4_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 3,
    "worker_primal": 664.008983,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 207,
    "baseline_csv": "BPC_future/results/gat_target_priority_worker_ab_family_20260614/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_9f2ee06df420d2ac_4_12_no_learning_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 3,
    "baseline_fallback_used": false,
    "baseline_primal": 664.008983,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 0,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "9f2ee06df420d2ac",
    "generated_sequences_delta": 3,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_9f2ee06df420d2ac_4_12",
    "official_bound_effect": false,
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi",
    "target_arc_option_sequence": [
      "0->4:low_risk:2",
      "4->12:low_risk:2",
      "12->0:low_risk:2"
    ],
    "target_sequence": [
      4,
      12
    ],
    "worker_columns": 207,
    "worker_csv": "BPC_future/results/gat_target_priority_worker_ab_family_20260614/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_9f2ee06df420d2ac_4_12_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 3,
    "worker_primal": 664.008983,
    "worker_status": "TIME_LIMIT"
  }
]
```

## 判断

- `positive_primal_roi` 表示 worker primal 严格优于同实例 baseline；
- `no_observed_roi` 表示 worker 与 baseline 没有可观测改善；
- 只要正负 ROI 同时存在，GAT HIGH_PRIORITY 就不能直接默认触发 worker；
- 所有结果都不能参与 no-negative certificate 或 official lower bound。
