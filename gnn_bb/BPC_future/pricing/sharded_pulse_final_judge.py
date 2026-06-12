"""Phase-1/2 scaffolding for the sharded Pulse final judge.

This module deliberately does not implement Pulse DFS.  It only models the
certificate ledger, cache-key identity, and a dummy shard engine that lets the
driver exercise exact-safe result semantics behind an opt-in switch.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
from typing import Any, Iterable


class ShardProofStatus(str, Enum):
    UNTOUCHED = "UNTOUCHED"
    RUNNING = "RUNNING"
    REFINED = "REFINED"
    FOUND_NEGATIVE = "FOUND_NEGATIVE"
    CERTIFIED_NO_NEGATIVE = "CERTIFIED_NO_NEGATIVE"
    DUPLICATE_ONLY = "DUPLICATE_ONLY"
    INCOMPLETE = "INCOMPLETE"
    INCOMPLETE_TIME_LIMIT = "INCOMPLETE_TIME_LIMIT"
    INCOMPLETE_RECURSION_LIMIT = "INCOMPLETE_RECURSION_LIMIT"
    INCOMPLETE_UNSUPPORTED_BRANCH = "INCOMPLETE_UNSUPPORTED_BRANCH"
    INCOMPLETE_CACHE_INVALID = "INCOMPLETE_CACHE_INVALID"
    DISABLED = "DISABLED"

    @classmethod
    def parse(cls, value: "ShardProofStatus | str") -> "ShardProofStatus":
        if isinstance(value, ShardProofStatus):
            return value
        normalized = str(value or "").strip().upper()
        aliases = {
            "CERTIFIED": cls.CERTIFIED_NO_NEGATIVE,
            "NEGATIVE": cls.FOUND_NEGATIVE,
            "FOUND": cls.FOUND_NEGATIVE,
            "TIME_LIMIT": cls.INCOMPLETE_TIME_LIMIT,
            "UNSUPPORTED": cls.INCOMPLETE_UNSUPPORTED_BRANCH,
            "CACHE_INVALID": cls.INCOMPLETE_CACHE_INVALID,
            "DUPLICATE": cls.DUPLICATE_ONLY,
        }
        if normalized in aliases:
            return aliases[normalized]
        return cls(normalized)


@dataclass(frozen=True)
class ShardCacheKey:
    instance_id: str
    branch_constraints_hash: str
    true_dual_hash: str
    cut_hash: str
    forbidden_signature_hash: str
    pricing_config_hash: str
    shard_id: str
    certificate_mode: str
    schema_version: str = "sharded_pulse_ledger_v1"
    proof_version: str = "pulse_proof_rules_v1"
    branch_depth: int = 0
    branch_state_key: tuple[Any, ...] = tuple()

    @classmethod
    def from_context(
        cls,
        *,
        instance_id: str,
        branch_constraints: Any,
        true_duals: Any,
        cuts: Any,
        forbidden_signatures: Any,
        pricing_config: Any,
        shard_id: str,
        certificate_mode: str = "sharded_pulse_v1",
        schema_version: str = "sharded_pulse_ledger_v1",
        proof_version: str = "pulse_proof_rules_v1",
        branch_depth: int = 0,
        branch_state_key: Iterable[Any] = tuple(),
    ) -> "ShardCacheKey":
        return cls(
            instance_id=str(instance_id),
            branch_constraints_hash=_stable_hash(branch_constraints),
            true_dual_hash=_stable_hash(true_duals),
            cut_hash=_stable_hash(cuts),
            forbidden_signature_hash=_stable_hash(forbidden_signatures),
            pricing_config_hash=_stable_hash(pricing_config),
            shard_id=str(shard_id),
            certificate_mode=str(certificate_mode),
            schema_version=str(schema_version),
            proof_version=str(proof_version),
            branch_depth=int(branch_depth),
            branch_state_key=tuple(branch_state_key or tuple()),
        )


@dataclass(frozen=True)
class ShardProofRecord:
    shard_id: str
    status: ShardProofStatus | str
    required: bool = True
    parent_id: str | None = None
    child_ids: tuple[str, ...] = tuple()
    proof_closed: bool = False
    frontier_state_count: int = 0
    reason: str = ""
    negative_count: int = 0
    stats: dict[str, Any] = field(default_factory=dict)

    @property
    def normalized_status(self) -> ShardProofStatus:
        return ShardProofStatus.parse(self.status)


@dataclass
class ShardLedger:
    records: dict[str, ShardProofRecord] = field(default_factory=dict)

    def add(self, record: ShardProofRecord) -> None:
        self.records[str(record.shard_id)] = record

    def aggregate_shard_status(self, shard_id: str, _seen: set[str] | None = None) -> ShardProofStatus:
        seen = set() if _seen is None else set(_seen)
        key = str(shard_id)
        if key in seen:
            return ShardProofStatus.INCOMPLETE_CACHE_INVALID
        seen.add(key)
        record = self.records.get(key)
        if record is None:
            return ShardProofStatus.INCOMPLETE_CACHE_INVALID
        status = record.normalized_status
        if status == ShardProofStatus.REFINED:
            child_statuses = [
                self.aggregate_shard_status(child_id, seen)
                for child_id in record.child_ids
                if self.records.get(str(child_id), record).required
            ]
            return _aggregate_statuses(child_statuses)
        if status == ShardProofStatus.CERTIFIED_NO_NEGATIVE and not bool(record.proof_closed):
            return ShardProofStatus.INCOMPLETE_CACHE_INVALID
        return status

    def global_status(self) -> ShardProofStatus:
        roots = [
            record
            for record in self.records.values()
            if bool(record.required) and record.parent_id is None
        ]
        return _aggregate_statuses(
            [self.aggregate_shard_status(record.shard_id) for record in roots]
        )

    def is_global_certificate(self) -> bool:
        return self.global_status() == ShardProofStatus.CERTIFIED_NO_NEGATIVE

    def counts(self) -> dict[str, int]:
        root_statuses = [
            self.aggregate_shard_status(record.shard_id)
            for record in self.records.values()
            if bool(record.required) and record.parent_id is None
        ]
        return {
            "total": len(root_statuses),
            "certified": sum(status == ShardProofStatus.CERTIFIED_NO_NEGATIVE for status in root_statuses),
            "incomplete": sum(_status_is_incomplete(status) for status in root_statuses),
            "negative_found": sum(status == ShardProofStatus.FOUND_NEGATIVE for status in root_statuses),
            "refined": sum(
                record.normalized_status == ShardProofStatus.REFINED
                for record in self.records.values()
                if bool(record.required)
            ),
            "duplicate_only": sum(status == ShardProofStatus.DUPLICATE_ONLY for status in root_statuses),
        }

    def result_fields(self) -> dict[str, Any]:
        status = self.global_status()
        counts = self.counts()
        fields: dict[str, Any] = {
            "global_certificate_capable": status == ShardProofStatus.CERTIFIED_NO_NEGATIVE,
            "final_judge_engine": "sharded_pulse",
            "final_judge_certificate_capable": status == ShardProofStatus.CERTIFIED_NO_NEGATIVE,
            "final_judge_sharded_enabled": True,
            "final_judge_shards_total": int(counts["total"]),
            "final_judge_shards_certified": int(counts["certified"]),
            "final_judge_shards_incomplete": int(counts["incomplete"]),
            "final_judge_shards_negative_found": int(counts["negative_found"]),
            "final_judge_shards_refined": int(counts["refined"]),
            "final_judge_incomplete_reason": "" if status == ShardProofStatus.CERTIFIED_NO_NEGATIVE else status.value,
        }
        if status == ShardProofStatus.CERTIFIED_NO_NEGATIVE:
            return {
                **fields,
                "exhausted": True,
                "best_reduced_cost": 0.0,
                "status": "OPTIMAL",
                "reason": "sharded_pulse_no_negative_journey",
                "pricing_state": "CERTIFIED_NO_NEGATIVE",
            }
        if status == ShardProofStatus.FOUND_NEGATIVE:
            return {
                **fields,
                "exhausted": False,
                "best_reduced_cost": None,
                "status": "FOUND_NEGATIVE",
                "reason": "sharded_pulse_found_negative",
                "pricing_state": "FOUND_NEGATIVE",
            }
        if status == ShardProofStatus.DUPLICATE_ONLY:
            return {
                **fields,
                "exhausted": False,
                "best_reduced_cost": None,
                "status": "INCOMPLETE",
                "reason": "sharded_pulse_duplicate_only_no_certificate",
                "pricing_state": "DUPLICATE_ONLY",
            }
        return {
            **fields,
            "exhausted": False,
            "best_reduced_cost": None,
            "status": "INCOMPLETE",
            "reason": "sharded_pulse_incomplete",
            "pricing_state": "INCOMPLETE_LIMIT",
        }


def build_dummy_shard_ledger(data: Any, dummy_statuses: Iterable[Any] | str | None = None) -> ShardLedger:
    """Build a controllable ledger for Phase-2 driver integration tests."""

    statuses = _dummy_status_sequence(dummy_statuses)
    tasks = tuple(int(task) for task in getattr(data, "tasks", tuple()))
    if not statuses:
        statuses = (ShardProofStatus.INCOMPLETE,)
    ledger = ShardLedger()
    for index, status in enumerate(statuses):
        shard_task = tasks[index] if index < len(tasks) else index + 1
        parsed = ShardProofStatus.parse(status)
        ledger.add(
            ShardProofRecord(
                shard_id=f"first_task:{shard_task}",
                status=parsed,
                proof_closed=parsed == ShardProofStatus.CERTIFIED_NO_NEGATIVE,
                reason="dummy_shard_engine",
                negative_count=1 if parsed == ShardProofStatus.FOUND_NEGATIVE else 0,
            )
        )
    return ledger


def _aggregate_statuses(statuses: Iterable[ShardProofStatus]) -> ShardProofStatus:
    values = tuple(statuses)
    if not values:
        return ShardProofStatus.INCOMPLETE_CACHE_INVALID
    if any(status == ShardProofStatus.FOUND_NEGATIVE for status in values):
        return ShardProofStatus.FOUND_NEGATIVE
    if all(status == ShardProofStatus.CERTIFIED_NO_NEGATIVE for status in values):
        return ShardProofStatus.CERTIFIED_NO_NEGATIVE
    if any(_status_is_incomplete(status) for status in values):
        return next(status for status in values if _status_is_incomplete(status))
    if any(status == ShardProofStatus.DUPLICATE_ONLY for status in values):
        return ShardProofStatus.DUPLICATE_ONLY
    return ShardProofStatus.INCOMPLETE


def _status_is_incomplete(status: ShardProofStatus) -> bool:
    return status in {
        ShardProofStatus.UNTOUCHED,
        ShardProofStatus.RUNNING,
        ShardProofStatus.INCOMPLETE,
        ShardProofStatus.INCOMPLETE_TIME_LIMIT,
        ShardProofStatus.INCOMPLETE_RECURSION_LIMIT,
        ShardProofStatus.INCOMPLETE_UNSUPPORTED_BRANCH,
        ShardProofStatus.INCOMPLETE_CACHE_INVALID,
        ShardProofStatus.DISABLED,
    }


def _dummy_status_sequence(values: Iterable[Any] | str | None) -> tuple[ShardProofStatus, ...]:
    if values is None:
        return tuple()
    if isinstance(values, str):
        values = tuple(part.strip() for part in values.split(",") if part.strip())
    return tuple(ShardProofStatus.parse(value) for value in values)


def _stable_hash(value: Any) -> str:
    payload = _normalize_for_hash(value)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _normalize_for_hash(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, dict):
        return {str(key): _normalize_for_hash(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (set, frozenset)):
        return sorted((_normalize_for_hash(item) for item in value), key=repr)
    if isinstance(value, (list, tuple)):
        return [_normalize_for_hash(item) for item in value]
    if hasattr(value, "__dataclass_fields__"):
        return {
            str(name): _normalize_for_hash(getattr(value, name))
            for name in sorted(value.__dataclass_fields__)  # type: ignore[attr-defined]
        }
    if hasattr(value, "__dict__"):
        return {
            str(name): _normalize_for_hash(item)
            for name, item in sorted(vars(value).items(), key=lambda pair: str(pair[0]))
            if not name.startswith("_")
        }
    return repr(value)
