"""Low-overhead resource guard for generation, training, and evaluation CLIs."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shutil


@dataclass(frozen=True)
class ResourceSnapshot:
    cpu_count: int
    load_1m: float
    memory_available_bytes: int
    disk_available_bytes: int

    @property
    def load_fraction(self) -> float:
        return self.load_1m / max(1, self.cpu_count)


def resource_snapshot(path: str | Path = ".") -> ResourceSnapshot:
    cpu_count = max(1, int(os.cpu_count() or 1))
    try:
        load_1m = float(os.getloadavg()[0])
    except (AttributeError, OSError):
        load_1m = 0.0
    memory_available = 0
    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            if line.startswith("MemAvailable:"):
                memory_available = int(line.split()[1]) * 1024
                break
    except OSError:
        pass
    disk_available = shutil.disk_usage(Path(path).resolve()).free
    return ResourceSnapshot(
        cpu_count=cpu_count,
        load_1m=load_1m,
        memory_available_bytes=memory_available,
        disk_available_bytes=disk_available,
    )


def recommended_parallelism(
    snapshot: ResourceSnapshot,
    *,
    requested: int = 4,
    min_memory_per_worker_bytes: int = 1024**3,
    min_disk_free_bytes: int = 10 * 1024**3,
) -> int:
    if snapshot.disk_available_bytes < min_disk_free_bytes:
        return 1
    memory_workers = (
        max(1, snapshot.memory_available_bytes // min_memory_per_worker_bytes)
        if snapshot.memory_available_bytes > 0
        else 1
    )
    idle_cpu = max(
        1, int(snapshot.cpu_count * max(0.1, 1.0 - snapshot.load_fraction))
    )
    return max(
        1,
        min(
            int(requested),
            snapshot.cpu_count,
            int(memory_workers),
            idle_cpu,
        ),
    )
