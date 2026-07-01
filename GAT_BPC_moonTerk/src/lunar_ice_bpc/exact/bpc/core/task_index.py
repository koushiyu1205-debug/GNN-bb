"""String-preserving task id to bit-mask mapping."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable, Mapping


@dataclass(frozen=True)
class TaskIndexMap:
    """Map external string task ids to compact internal indices and bits."""

    external_ids: tuple[str, ...]

    def __init__(self, external_ids: Iterable[object]) -> None:
        ids = tuple(str(task_id) for task_id in external_ids)
        if len(set(ids)) != len(ids):
            duplicates = sorted({task_id for task_id in ids if ids.count(task_id) > 1})
            raise ValueError(f"duplicate task ids: {duplicates}")
        object.__setattr__(self, "external_ids", ids)
        object.__setattr__(
            self,
            "_index_by_external_id",
            MappingProxyType({task_id: index for index, task_id in enumerate(ids)}),
        )

    @classmethod
    def from_tasks(cls, tasks: Mapping[object, object]) -> "TaskIndexMap":
        return cls(sorted(str(task_id) for task_id in tasks))

    @property
    def index_by_external_id(self) -> Mapping[str, int]:
        return self._index_by_external_id

    @property
    def full_mask(self) -> int:
        return (1 << len(self.external_ids)) - 1

    def __len__(self) -> int:
        return len(self.external_ids)

    def external_id_to_index(self, task_id: object) -> int:
        key = str(task_id)
        if key not in self._index_by_external_id:
            raise KeyError(f"unknown task id: {key}")
        return int(self._index_by_external_id[key])

    def index_to_external_id(self, index: int) -> str:
        value = int(index)
        if value < 0 or value >= len(self.external_ids):
            raise IndexError(f"task index out of range: {index}")
        return self.external_ids[value]

    def bit_of(self, task_id: object) -> int:
        return 1 << self.external_id_to_index(task_id)

    def mask_of(self, task_id: object) -> int:
        return self.bit_of(task_id)

    def mask_from_ids(self, task_ids: Iterable[object]) -> int:
        mask = 0
        for task_id in task_ids:
            mask |= self.mask_of(task_id)
        return mask

    def ids_from_mask(self, mask: int) -> tuple[str, ...]:
        self.require_mask(mask)
        bits = int(mask)
        ids: list[str] = []
        index = 0
        while bits:
            if bits & 1:
                ids.append(self.index_to_external_id(index))
            bits >>= 1
            index += 1
        return tuple(ids)

    def require_mask(self, mask: int) -> int:
        value = int(mask)
        if value < 0:
            raise ValueError(f"task mask must be nonnegative: {mask}")
        extra_bits = value & ~self.full_mask
        if extra_bits:
            raise ValueError(f"task mask contains bits outside task universe: {mask}")
        return value

