# CBF Mode Transition Audit 报告

日期：2026-06-14

## 目的

本报告只从已有 JSONL 中重建 `state_t, action_t, state_{t+1}` transition，
计算 Lyapunov surrogate 与 CBF barrier slack。它不运行 BPC / pricing / RMP / Pulse，
也不改变 worker、certificate 或 official lower bound。

## 机器字段

```text
cbf_mode_transition_audit = current
diagnostic_only = true
runs_bpc_or_pricing = false
status = cbf_mode_transition_audited
all_checks_pass = true
production_ready = false
goal_complete = false
```

## 摘要

```json
{
  "bad_capture_event_count": 0,
  "bad_mode_transition_count": 1,
  "capture_event_count": 6,
  "cbf_feasible_observed_count": 3,
  "cbf_infeasible_observed_count": 1,
  "has_transition_evidence": true,
  "input_file_count": 1,
  "mode_switch_count": 4,
  "negative_action_transition_count": 4,
  "training_ready": false,
  "transition_count": 4,
  "transition_task_count_histogram": {
    "4": 4
  }
}
```

## 检查项

```json
{
  "all_capture_events_no_certificate_effect": true,
  "barrier_values_are_present": true,
  "diagnostic_only": true,
  "no_decode_errors": true,
  "runs_bpc_or_pricing_false": true,
  "transitions_have_state_action_next": true
}
```

## 解释

- `cbf_feasible_observed_count` 只表示相邻 capture 事件在该 surrogate 下满足离散 CBF slack；
- `cbf_infeasible_observed_count` 表示当前 observed action 后 energy 没有满足该安全约束；
- 本报告不能证明 production speedup，也不能作为 certificate；
- 下一步应扩大 no-certificate-effect capture，覆盖 5/10/20 多实例和 mixed/noop/improved contexts。

## Transition samples

```json
[
  {
    "action_first_second": [
      [
        "1",
        "2"
      ]
    ],
    "action_negative_count": 1,
    "action_returned_count": 1,
    "action_task_sets": [
      [
        1,
        2,
        3,
        4
      ]
    ],
    "active_hash_before": "9903e4767d6f3fe3",
    "active_hash_next": "d745e029352b0c32",
    "active_hash_switched": true,
    "alpha": 0.25,
    "bad_mode_transition": true,
    "barrier_slack": -101.289839802,
    "cbf_feasible_observed": false,
    "cg_iter": 1,
    "context_hash": "95b6e06e65c2f8dd",
    "delta_v": 100.888974328,
    "depth": 0,
    "h_next": -102.492436224,
    "h_t": -1.603461896,
    "instance": "very_small",
    "mode_switched": true,
    "next_cg_iter": 2,
    "next_context_hash": "9e19b2e71929ff7f",
    "node_id": 0,
    "source_file": "BPC_future/results/cbf_mode_transition_capture_smoke_20260614/logs/very_small.jsonl",
    "state_next_mode": {
      "active_hash": "d745e029352b0c32",
      "best_true_rc": -4.669162,
      "first_task_hist": {
        "1": 6,
        "2": 3,
        "3": 2,
        "4": 1
      },
      "mode_entropy": 3.409102890534595,
      "negative_count": 1,
      "observed_journey_count": 12,
      "pool_signature_hash": "dd9c78911ea426aa",
      "pool_task_set_hash": "a975afe952cd03f5",
      "replacement_ratio": 0.0,
      "returned_journey_count": 1,
      "second_action_hist": {
        "1->2": 3,
        "1->3": 1,
        "1->4": 1,
        "1->return": 1,
        "2->3": 1,
        "2->4": 1,
        "2->return": 1,
        "3->4": 1,
        "3->return": 1,
        "4->return": 1
      },
      "support_changing_ratio": 1.0,
      "task_set_size_hist": {
        "1": 4,
        "2": 7,
        "4": 1
      },
      "z_hash": "('d745e029352b0c32', 'dd9c78911ea426aa', \"(('1', 6), ('2', 3), ('3', 2), ('4', 1))\", \"(('1->2', 3), ('1->3', 1), ('1->4', 1), ('1->return', 1), ('2->3', 1), ('2->4', 1), ('2->return', 1), ('3->4', 1), ('3->return', 1), ('4->return', 1))\", \"(('1', 4), ('2', 7), ('4', 1))\")"
    },
    "state_next_z_hash": "('d745e029352b0c32', 'dd9c78911ea426aa', \"(('1', 6), ('2', 3), ('3', 2), ('4', 1))\", \"(('1->2', 3), ('1->3', 1), ('1->4', 1), ('1->return', 1), ('2->3', 1), ('2->4', 1), ('2->return', 1), ('3->4', 1), ('3->return', 1), ('4->return', 1))\", \"(('1', 4), ('2', 7), ('4', 1))\")",
    "state_t_mode": {
      "active_hash": "9903e4767d6f3fe3",
      "best_true_rc": -112.300784,
      "first_task_hist": {
        "1": 5,
        "2": 3,
        "3": 2,
        "4": 1
      },
      "mode_entropy": 3.5125528046499586,
      "negative_count": 1,
      "observed_journey_count": 11,
      "pool_signature_hash": "ed6f945731619c4b",
      "pool_task_set_hash": "3c7c315bdbd325d6",
      "replacement_ratio": 0.0,
      "returned_journey_count": 1,
      "second_action_hist": {
        "1->2": 2,
        "1->3": 1,
        "1->4": 1,
        "1->return": 1,
        "2->3": 1,
        "2->4": 1,
        "2->return": 1,
        "3->4": 1,
        "3->return": 1,
        "4->return": 1
      },
      "support_changing_ratio": 1.0,
      "task_set_size_hist": {
        "1": 4,
        "2": 6,
        "4": 1
      },
      "z_hash": "('9903e4767d6f3fe3', 'ed6f945731619c4b', \"(('1', 5), ('2', 3), ('3', 2), ('4', 1))\", \"(('1->2', 2), ('1->3', 1), ('1->4', 1), ('1->return', 1), ('2->3', 1), ('2->4', 1), ('2->return', 1), ('3->4', 1), ('3->return', 1), ('4->return', 1))\", \"(('1', 4), ('2', 6), ('4', 1))\")"
    },
    "state_t_z_hash": "('9903e4767d6f3fe3', 'ed6f945731619c4b', \"(('1', 5), ('2', 3), ('3', 2), ('4', 1))\", \"(('1->2', 2), ('1->3', 1), ('1->4', 1), ('1->return', 1), ('2->3', 1), ('2->4', 1), ('2->return', 1), ('3->4', 1), ('3->return', 1), ('4->return', 1))\", \"(('1', 4), ('2', 6), ('4', 1))\")",
    "task_count": 4,
    "v_crit": 1.0,
    "v_next": 103.492436224,
    "v_next_components": {
      "basis_turnover": 1.0,
      "dual_l1_delta": 212.300784,
      "final_judge_retry_count": 0.0,
      "hidden_negative_count": 0.083333333,
      "objective_progress": 112.300784,
      "replacement_ratio": 0.0,
      "residual_mode_entropy": 3.409102891,
      "support_changing_progress": 1.0
    },
    "v_t": 2.603461896,
    "v_t_components": {
      "basis_turnover": 0.0,
      "dual_l1_delta": 0.0,
      "final_judge_retry_count": 0.0,
      "hidden_negative_count": 0.090909091,
      "objective_progress": 0.0,
      "replacement_ratio": 0.0,
      "residual_mode_entropy": 3.512552805,
      "support_changing_progress": 1.0
    }
  },
  {
    "action_first_second": [
      [
        "1",
        "2"
      ]
    ],
    "action_negative_count": 1,
    "action_returned_count": 1,
    "action_task_sets": [
      [
        1,
        2
      ]
    ],
    "active_hash_before": "d745e029352b0c32",
    "active_hash_next": "d745e029352b0c32",
    "active_hash_switched": false,
    "alpha": 0.25,
    "bad_mode_transition": false,
    "barrier_slack": 64.994962932,
    "cbf_feasible_observed": true,
    "cg_iter": 2,
    "context_hash": "9e19b2e71929ff7f",
    "delta_v": -90.618071988,
    "depth": 0,
    "h_next": -11.874364236,
    "h_t": -102.492436224,
    "instance": "very_small",
    "mode_switched": true,
    "next_cg_iter": 3,
    "next_context_hash": "c7a919efb6622c29",
    "node_id": 0,
    "source_file": "BPC_future/results/cbf_mode_transition_capture_smoke_20260614/logs/very_small.jsonl",
    "state_next_mode": {
      "active_hash": "d745e029352b0c32",
      "best_true_rc": -2.541578,
      "first_task_hist": {
        "1": 6,
        "2": 3,
        "3": 2,
        "4": 1
      },
      "mode_entropy": 3.4527069025149735,
      "negative_count": 1,
      "observed_journey_count": 12,
      "pool_signature_hash": "a47bc9acd5c840df",
      "pool_task_set_hash": "a975afe952cd03f5",
      "replacement_ratio": 0.0,
      "returned_journey_count": 1,
      "second_action_hist": {
        "1->2": 2,
        "1->3": 2,
        "1->4": 1,
        "1->return": 1,
        "2->3": 1,
        "2->4": 1,
        "2->return": 1,
        "3->4": 1,
        "3->return": 1,
        "4->return": 1
      },
      "support_changing_ratio": 1.0,
      "task_set_size_hist": {
        "1": 4,
        "2": 7,
        "4": 1
      },
      "z_hash": "('d745e029352b0c32', 'a47bc9acd5c840df', \"(('1', 6), ('2', 3), ('3', 2), ('4', 1))\", \"(('1->2', 2), ('1->3', 2), ('1->4', 1), ('1->return', 1), ('2->3', 1), ('2->4', 1), ('2->return', 1), ('3->4', 1), ('3->return', 1), ('4->return', 1))\", \"(('1', 4), ('2', 7), ('4', 1))\")"
    },
    "state_next_z_hash": "('d745e029352b0c32', 'a47bc9acd5c840df', \"(('1', 6), ('2', 3), ('3', 2), ('4', 1))\", \"(('1->2', 2), ('1->3', 2), ('1->4', 1), ('1->return', 1), ('2->3', 1), ('2->4', 1), ('2->return', 1), ('3->4', 1), ('3->return', 1), ('4->return', 1))\", \"(('1', 4), ('2', 7), ('4', 1))\")",
    "state_t_mode": {
      "active_hash": "d745e029352b0c32",
      "best_true_rc": -4.669162,
      "first_task_hist": {
        "1": 6,
        "2": 3,
        "3": 2,
        "4": 1
      },
      "mode_entropy": 3.409102890534595,
      "negative_count": 1,
      "observed_journey_count": 12,
      "pool_signature_hash": "dd9c78911ea426aa",
      "pool_task_set_hash": "a975afe952cd03f5",
      "replacement_ratio": 0.0,
      "returned_journey_count": 1,
      "second_action_hist": {
        "1->2": 3,
        "1->3": 1,
        "1->4": 1,
        "1->return": 1,
        "2->3": 1,
        "2->4": 1,
        "2->return": 1,
        "3->4": 1,
        "3->return": 1,
        "4->return": 1
      },
      "support_changing_ratio": 1.0,
      "task_set_size_hist": {
        "1": 4,
        "2": 7,
        "4": 1
      },
      "z_hash": "('d745e029352b0c32', 'dd9c78911ea426aa', \"(('1', 6), ('2', 3), ('3', 2), ('4', 1))\", \"(('1->2', 3), ('1->3', 1), ('1->4', 1), ('1->return', 1), ('2->3', 1), ('2->4', 1), ('2->return', 1), ('3->4', 1), ('3->return', 1), ('4->return', 1))\", \"(('1', 4), ('2', 7), ('4', 1))\")"
    },
    "state_t_z_hash": "('d745e029352b0c32', 'dd9c78911ea426aa', \"(('1', 6), ('2', 3), ('3', 2), ('4', 1))\", \"(('1->2', 3), ('1->3', 1), ('1->4', 1), ('1->return', 1), ('2->3', 1), ('2->4', 1), ('2->return', 1), ('3->4', 1), ('3->return', 1), ('4->return', 1))\", \"(('1', 4), ('2', 7), ('4', 1))\")",
    "task_count": 4,
    "v_crit": 1.0,
    "v_next": 12.874364236,
    "v_next_components": {
      "basis_turnover": 0.0,
      "dual_l1_delta": 9.338324,
      "final_judge_retry_count": 1.0,
      "hidden_negative_count": 0.083333333,
      "objective_progress": 0.0,
      "replacement_ratio": 0.0,
      "residual_mode_entropy": 3.452706903,
      "support_changing_progress": 1.0
    },
    "v_t": 103.492436224,
    "v_t_components": {
      "basis_turnover": 1.0,
      "dual_l1_delta": 212.300784,
      "final_judge_retry_count": 0.0,
      "hidden_negative_count": 0.083333333,
      "objective_progress": 112.300784,
      "replacement_ratio": 0.0,
      "residual_mode_entropy": 3.409102891,
      "support_changing_progress": 1.0
    }
  },
  {
    "action_first_second": [
      [
        "1",
        "3"
      ]
    ],
    "action_negative_count": 1,
    "action_returned_count": 1,
    "action_task_sets": [
      [
        1,
        3
      ]
    ],
    "active_hash_before": "d745e029352b0c32",
    "active_hash_next": "d745e029352b0c32",
    "active_hash_switched": false,
    "alpha": 0.25,
    "bad_mode_transition": false,
    "barrier_slack": 0.286576941,
    "cbf_feasible_observed": true,
    "cg_iter": 3,
    "context_hash": "c7a919efb6622c29",
    "delta_v": -3.255168,
    "depth": 0,
    "h_next": -8.619196236,
    "h_t": -11.874364236,
    "instance": "very_small",
    "mode_switched": true,
    "next_cg_iter": 4,
    "next_context_hash": "fed7b68a17754c2e",
    "node_id": 0,
    "source_file": "BPC_future/results/cbf_mode_transition_capture_smoke_20260614/logs/very_small.jsonl",
    "state_next_mode": {
      "active_hash": "d745e029352b0c32",
      "best_true_rc": -0.114096,
      "first_task_hist": {
        "1": 6,
        "2": 3,
        "3": 2,
        "4": 1
      },
      "mode_entropy": 3.4527069025149735,
      "negative_count": 1,
      "observed_journey_count": 12,
      "pool_signature_hash": "25297004d7da63a9",
      "pool_task_set_hash": "a975afe952cd03f5",
      "replacement_ratio": 0.0,
      "returned_journey_count": 1,
      "second_action_hist": {
        "1->2": 2,
        "1->3": 1,
        "1->4": 2,
        "1->return": 1,
        "2->3": 1,
        "2->4": 1,
        "2->return": 1,
        "3->4": 1,
        "3->return": 1,
        "4->return": 1
      },
      "support_changing_ratio": 1.0,
      "task_set_size_hist": {
        "1": 4,
        "2": 7,
        "4": 1
      },
      "z_hash": "('d745e029352b0c32', '25297004d7da63a9', \"(('1', 6), ('2', 3), ('3', 2), ('4', 1))\", \"(('1->2', 2), ('1->3', 1), ('1->4', 2), ('1->return', 1), ('2->3', 1), ('2->4', 1), ('2->return', 1), ('3->4', 1), ('3->return', 1), ('4->return', 1))\", \"(('1', 4), ('2', 7), ('4', 1))\")"
    },
    "state_next_z_hash": "('d745e029352b0c32', '25297004d7da63a9', \"(('1', 6), ('2', 3), ('3', 2), ('4', 1))\", \"(('1->2', 2), ('1->3', 1), ('1->4', 2), ('1->return', 1), ('2->3', 1), ('2->4', 1), ('2->return', 1), ('3->4', 1), ('3->return', 1), ('4->return', 1))\", \"(('1', 4), ('2', 7), ('4', 1))\")",
    "state_t_mode": {
      "active_hash": "d745e029352b0c32",
      "best_true_rc": -2.541578,
      "first_task_hist": {
        "1": 6,
        "2": 3,
        "3": 2,
        "4": 1
      },
      "mode_entropy": 3.4527069025149735,
      "negative_count": 1,
      "observed_journey_count": 12,
      "pool_signature_hash": "a47bc9acd5c840df",
      "pool_task_set_hash": "a975afe952cd03f5",
      "replacement_ratio": 0.0,
      "returned_journey_count": 1,
      "second_action_hist": {
        "1->2": 2,
        "1->3": 2,
        "1->4": 1,
        "1->return": 1,
        "2->3": 1,
        "2->4": 1,
        "2->return": 1,
        "3->4": 1,
        "3->return": 1,
        "4->return": 1
      },
      "support_changing_ratio": 1.0,
      "task_set_size_hist": {
        "1": 4,
        "2": 7,
        "4": 1
      },
      "z_hash": "('d745e029352b0c32', 'a47bc9acd5c840df', \"(('1', 6), ('2', 3), ('3', 2), ('4', 1))\", \"(('1->2', 2), ('1->3', 2), ('1->4', 1), ('1->return', 1), ('2->3', 1), ('2->4', 1), ('2->return', 1), ('3->4', 1), ('3->return', 1), ('4->return', 1))\", \"(('1', 4), ('2', 7), ('4', 1))\")"
    },
    "state_t_z_hash": "('d745e029352b0c32', 'a47bc9acd5c840df', \"(('1', 6), ('2', 3), ('3', 2), ('4', 1))\", \"(('1->2', 2), ('1->3', 2), ('1->4', 1), ('1->return', 1), ('2->3', 1), ('2->4', 1), ('2->return', 1), ('3->4', 1), ('3->return', 1), ('4->return', 1))\", \"(('1', 4), ('2', 7), ('4', 1))\")",
    "task_count": 4,
    "v_crit": 1.0,
    "v_next": 9.619196236,
    "v_next_components": {
      "basis_turnover": 0.0,
      "dual_l1_delta": 5.083156,
      "final_judge_retry_count": 2.0,
      "hidden_negative_count": 0.083333333,
      "objective_progress": 0.0,
      "replacement_ratio": 0.0,
      "residual_mode_entropy": 3.452706903,
      "support_changing_progress": 1.0
    },
    "v_t": 12.874364236,
    "v_t_components": {
      "basis_turnover": 0.0,
      "dual_l1_delta": 9.338324,
      "final_judge_retry_count": 1.0,
      "hidden_negative_count": 0.083333333,
      "objective_progress": 0.0,
      "replacement_ratio": 0.0,
      "residual_mode_entropy": 3.452706903,
      "support_changing_progress": 1.0
    }
  },
  {
    "action_first_second": [
      [
        "1",
        "4"
      ]
    ],
    "action_negative_count": 1,
    "action_returned_count": 1,
    "action_task_sets": [
      [
        1,
        4
      ]
    ],
    "active_hash_before": "d745e029352b0c32",
    "active_hash_next": "d745e029352b0c32",
    "active_hash_switched": false,
    "alpha": 0.25,
    "bad_mode_transition": false,
    "barrier_slack": 0.723652372,
    "cbf_feasible_observed": true,
    "cg_iter": 4,
    "context_hash": "fed7b68a17754c2e",
    "delta_v": -2.878451431,
    "depth": 0,
    "h_next": -5.740744805,
    "h_t": -8.619196236,
    "instance": "very_small",
    "mode_switched": true,
    "next_cg_iter": 5,
    "next_context_hash": "a566d0915b86ffab",
    "node_id": 0,
    "source_file": "BPC_future/results/cbf_mode_transition_capture_smoke_20260614/logs/very_small.jsonl",
    "state_next_mode": {
      "active_hash": "d745e029352b0c32",
      "best_true_rc": 0.0,
      "first_task_hist": {
        "1": 5,
        "2": 3,
        "3": 2,
        "4": 1
      },
      "mode_entropy": 3.5125528046499586,
      "negative_count": 0,
      "observed_journey_count": 11,
      "pool_signature_hash": "e5ccef6667f898df",
      "pool_task_set_hash": "a975afe952cd03f5",
      "replacement_ratio": 0.0,
      "returned_journey_count": 0,
      "second_action_hist": {
        "1->2": 2,
        "1->3": 1,
        "1->4": 1,
        "1->return": 1,
        "2->3": 1,
        "2->4": 1,
        "2->return": 1,
        "3->4": 1,
        "3->return": 1,
        "4->return": 1
      },
      "support_changing_ratio": 0.0,
      "task_set_size_hist": {
        "1": 4,
        "2": 6,
        "4": 1
      },
      "z_hash": "('d745e029352b0c32', 'e5ccef6667f898df', \"(('1', 5), ('2', 3), ('3', 2), ('4', 1))\", \"(('1->2', 2), ('1->3', 1), ('1->4', 1), ('1->return', 1), ('2->3', 1), ('2->4', 1), ('2->return', 1), ('3->4', 1), ('3->return', 1), ('4->return', 1))\", \"(('1', 4), ('2', 6), ('4', 1))\")"
    },
    "state_next_z_hash": "('d745e029352b0c32', 'e5ccef6667f898df', \"(('1', 5), ('2', 3), ('3', 2), ('4', 1))\", \"(('1->2', 2), ('1->3', 1), ('1->4', 1), ('1->return', 1), ('2->3', 1), ('2->4', 1), ('2->return', 1), ('3->4', 1), ('3->return', 1), ('4->return', 1))\", \"(('1', 4), ('2', 6), ('4', 1))\")",
    "state_t_mode": {
      "active_hash": "d745e029352b0c32",
      "best_true_rc": -0.114096,
      "first_task_hist": {
        "1": 6,
        "2": 3,
        "3": 2,
        "4": 1
      },
      "mode_entropy": 3.4527069025149735,
      "negative_count": 1,
      "observed_journey_count": 12,
      "pool_signature_hash": "25297004d7da63a9",
      "pool_task_set_hash": "a975afe952cd03f5",
      "replacement_ratio": 0.0,
      "returned_journey_count": 1,
      "second_action_hist": {
        "1->2": 2,
        "1->3": 1,
        "1->4": 2,
        "1->return": 1,
        "2->3": 1,
        "2->4": 1,
        "2->return": 1,
        "3->4": 1,
        "3->return": 1,
        "4->return": 1
      },
      "support_changing_ratio": 1.0,
      "task_set_size_hist": {
        "1": 4,
        "2": 7,
        "4": 1
      },
      "z_hash": "('d745e029352b0c32', '25297004d7da63a9', \"(('1', 6), ('2', 3), ('3', 2), ('4', 1))\", \"(('1->2', 2), ('1->3', 1), ('1->4', 2), ('1->return', 1), ('2->3', 1), ('2->4', 1), ('2->return', 1), ('3->4', 1), ('3->return', 1), ('4->return', 1))\", \"(('1', 4), ('2', 7), ('4', 1))\")"
    },
    "state_t_z_hash": "('d745e029352b0c32', '25297004d7da63a9', \"(('1', 6), ('2', 3), ('3', 2), ('4', 1))\", \"(('1->2', 2), ('1->3', 1), ('1->4', 2), ('1->return', 1), ('2->3', 1), ('2->4', 1), ('2->return', 1), ('3->4', 1), ('3->return', 1), ('4->return', 1))\", \"(('1', 4), ('2', 7), ('4', 1))\")",
    "task_count": 4,
    "v_crit": 1.0,
    "v_next": 6.740744805,
    "v_next_components": {
      "basis_turnover": 0.0,
      "dual_l1_delta": 0.228192,
      "final_judge_retry_count": 3.0,
      "hidden_negative_count": 0.0,
      "objective_progress": 0.0,
      "replacement_ratio": 0.0,
      "residual_mode_entropy": 3.512552805,
      "support_changing_progress": 0.0
    },
    "v_t": 9.619196236,
    "v_t_components": {
      "basis_turnover": 0.0,
      "dual_l1_delta": 5.083156,
      "final_judge_retry_count": 2.0,
      "hidden_negative_count": 0.083333333,
      "objective_progress": 0.0,
      "replacement_ratio": 0.0,
      "residual_mode_entropy": 3.452706903,
      "support_changing_progress": 1.0
    }
  }
]
```
