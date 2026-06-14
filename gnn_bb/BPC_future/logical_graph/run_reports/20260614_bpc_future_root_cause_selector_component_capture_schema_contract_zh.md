# Root Cause Selector Component Capture Schema Contract 报告

日期：2026-06-14

## 目的

本报告检查 selector component-context 所需字段在当前 capture JSONL 中的
实际存在形态：哪些是显式 payload，哪些只是 hash/count，哪些仍需扩展
采集 schema。它只读已有日志和 summary，不运行 BPC / pricing / RMP / Pulse。

## 机器字段

```text
selector_component_capture_schema_contract = current
diagnostic_only = true
runs_bpc_or_pricing = false
status = component_capture_schema_contract_audited
capture_file_count = 18
capture_event_count = 78
complete_active_basis_events = 78
complete_pool_events = 78
returned_batch_complete_events = 78
returned_batch_nonempty_events = 60
forbidden_explicit_events = 12
explicit_forbidden_signature_list_available = true
code_supports_explicit_forbidden_payload = true
holdout_runbook_enables_explicit_forbidden_payload = true
all_checks_pass = true
```

## 字段结论

### active_basis_snapshot

status = `captured_as_explicit_payload`

```json
{
  "complete_active_basis_events": 78,
  "event_count": 78,
  "field_stats": {
    "max_payload_len": 17,
    "nonempty_count": 78,
    "present_count": 78,
    "types": [
      "list"
    ]
  }
}
```

### pool_signature_composition

status = `captured_as_explicit_payload`

```json
{
  "complete_pool_events": 78,
  "event_count": 78,
  "pool_journeys": {
    "max_payload_len": 266,
    "nonempty_count": 78,
    "present_count": 78,
    "types": [
      "list"
    ]
  },
  "pool_signatures": {
    "max_payload_len": 266,
    "nonempty_count": 78,
    "present_count": 78,
    "types": [
      "list"
    ]
  },
  "pool_task_sets": {
    "max_payload_len": 266,
    "nonempty_count": 78,
    "present_count": 78,
    "types": [
      "list"
    ]
  }
}
```

### returned_batch_payload

status = `captured_as_explicit_payload_when_nonempty`

```json
{
  "returned_batch_complete_events": 78,
  "returned_batch_nonempty_events": 60,
  "returned_journeys": {
    "max_payload_len": 8,
    "nonempty_count": 60,
    "present_count": 78,
    "types": [
      "list"
    ]
  }
}
```

### forbidden_signature_pressure

status = `captured_as_explicit_payload`

```json
{
  "explicit_required_stats": {
    "forbidden_journey_signatures": {
      "max_payload_len": 0,
      "nonempty_count": 0,
      "present_count": 0,
      "types": []
    },
    "forbidden_signatures": {
      "max_payload_len": 180,
      "nonempty_count": 12,
      "present_count": 12,
      "types": [
        "list"
      ]
    }
  },
  "forbidden_explicit_events": 12,
  "forbidden_signature_count": {
    "max_payload_len": 0,
    "nonempty_count": 78,
    "present_count": 78,
    "types": [
      "int"
    ]
  },
  "forbidden_signature_hash": {
    "max_payload_len": 0,
    "nonempty_count": 78,
    "present_count": 78,
    "types": [
      "str"
    ]
  }
}
```

## 解释

Current config-matched selector-holdout capture events already carry explicit active-basis, pool, returned-batch, and forbidden-signature payloads.  The forbidden-signature payload is now observed in a targeted no-certificate-effect capture pass, so candidate-vs-forbidden overlap can be derived by the next selector-row builder.  This keeps component context work in calibration mode, not production mode.

这进一步收紧当前根因判断：selector 的下一步不是再调 worker，也不是
直接 production A/B，而是把已经实测落盘的 active/pool/returned/
forbidden component payload 转成 addition-before candidate rows 后
再做 holdout。

## 检查项

```json
{
  "active_basis_payload_complete": true,
  "capture_events_present": true,
  "code_supports_explicit_forbidden_payload": true,
  "component_readiness_passed": true,
  "context_schema_gap_passed": true,
  "explicit_forbidden_signature_list_available": true,
  "forbidden_hash_count_present": true,
  "holdout_runbook_enables_explicit_forbidden_payload": true,
  "pool_payload_complete": true,
  "pool_signatures_present": true,
  "returned_batch_flags_complete": true,
  "returned_batch_has_nonempty_examples": true,
  "selector_still_not_production_ready": true
}
```
